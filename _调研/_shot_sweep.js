/**
 * Screenshot sweep: navigate to each route, wait, capture a screenshot.
 * Usage: node _shot_sweep.js routes.json outdir [skipN] [limitN]
 */
const http = require('http'), net = require('net'), crypto = require('crypto'), fs = require('fs'), path = require('path');
const PORT = process.env.CDP_PORT || 9333;
const BASE = 'https://wy.365ymd.com';
const httpGet = p => new Promise((res, rej) =>
  http.get({ host: '127.0.0.1', port: PORT, path: p }, r => { let d = ''; r.on('data', c => d += c); r.on('end', () => res(d)); }).on('error', rej));

class WS {
  constructor(url) { const m = url.match(/^ws:\/\/([^:/]+):(\d+)(\/.*)$/); this.host = m[1]; this.port = +m[2]; this.path = m[3]; this.buf = Buffer.alloc(0); }
  connect() { return new Promise((resolve, reject) => {
    const key = crypto.randomBytes(16).toString('base64');
    this.sock = net.connect(this.port, this.host, () =>
      this.sock.write(`GET ${this.path} HTTP/1.1\r\nHost: ${this.host}:${this.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ${key}\r\nSec-WebSocket-Version: 13\r\n\r\n`));
    this.sock.on('error', reject); let hs = false;
    this.sock.on('data', ch => { this.buf = Buffer.concat([this.buf, ch]);
      if (!hs) { const i = this.buf.indexOf('\r\n\r\n'); if (i < 0) return;
        if (!/101/.test(this.buf.slice(0, i).toString())) return reject(new Error('handshake'));
        this.buf = this.buf.slice(i + 4); hs = true; resolve(); }
      this.drain(); });
  }); }
  drain() { for (;;) {
    if (this.buf.length < 2) return;
    const b1 = this.buf[1], op = this.buf[0] & 15, mk = (b1 & 128) !== 0;
    let len = b1 & 127, off = 2;
    if (len === 126) { if (this.buf.length < 4) return; len = this.buf.readUInt16BE(2); off = 4; }
    else if (len === 127) { if (this.buf.length < 10) return; len = Number(this.buf.readBigUInt64BE(2)); off = 10; }
    let k = null; if (mk) { if (this.buf.length < off + 4) return; k = this.buf.slice(off, off + 4); off += 4; }
    if (this.buf.length < off + len) return;
    let p = this.buf.slice(off, off + len);
    if (k) { p = Buffer.from(p); for (let i = 0; i < p.length; i++) p[i] ^= k[i % 4]; }
    this.buf = this.buf.slice(off + len);
    if (op === 1) { try { this.msg(JSON.parse(p.toString('utf8'))); } catch (e) {} }
    else if (op === 8) return;
    else if (op === 9) this.frame(p, 10);
  } }
  frame(pl, op = 1) { const d = Buffer.isBuffer(pl) ? pl : Buffer.from(pl, 'utf8'); let h;
    if (d.length < 126) { h = Buffer.alloc(2); h[1] = 128 | d.length; }
    else if (d.length < 65536) { h = Buffer.alloc(4); h[1] = 128 | 126; h.writeUInt16BE(d.length, 2); }
    else { h = Buffer.alloc(10); h[1] = 128 | 127; h.writeBigUInt64BE(BigInt(d.length), 2); }
    h[0] = 128 | op;
    const k = crypto.randomBytes(4), m = Buffer.from(d);
    for (let i = 0; i < m.length; i++) m[i] ^= k[i % 4];
    this.sock.write(Buffer.concat([h, k, m])); }
  send(o) { this.frame(JSON.stringify(o)); }
}
class CDP {
  constructor(ws) { this.ws = ws; this.id = 0; this.p = new Map();
    ws.msg = m => { if (m.id && this.p.has(m.id)) { const { res, rej } = this.p.get(m.id); this.p.delete(m.id);
      m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); } }; }
  send(method, params = {}) { const id = ++this.id;
    return new Promise((res, rej) => { this.p.set(id, { res, rej }); this.ws.send({ id, method, params });
      setTimeout(() => { if (this.p.has(id)) { this.p.delete(id); rej(new Error('timeout ' + method)); } }, 60000); }); }
  async eval(e, ap = false) { const r = await this.send('Runtime.evaluate',
    { expression: e, returnByValue: true, awaitPromise: ap, userGesture: true });
    return r && r.result ? r.result.value : undefined; }
}
async function connect() {
  const list = JSON.parse(await httpGet('/json/list'));
  const page = list.filter(t => t.type === 'page')[0];
  const ws = new WS(page.webSocketDebuggerUrl);
  await ws.connect();
  const cdp = new CDP(ws);
  await cdp.send('Runtime.enable');
  return { ws, cdp };
}

async function main() {
  const routes = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const outDir = process.argv[3];
  const skip = parseInt(process.argv[4] || '0', 10);
  const limit = parseInt(process.argv[5] || '999', 10);
  fs.mkdirSync(outDir, { recursive: true });

  const slice = routes.slice(skip, skip + limit);
  let { ws, cdp } = await connect();
  for (const r of slice) {
    const full = r.route.startsWith('http') ? r.route : BASE + r.route;
    try { await cdp.eval(`location.href = ${JSON.stringify(full)}; 'go'`, false); } catch (e) {}
    await new Promise(res => setTimeout(res, 11000));
    try { ws.sock.destroy(); } catch (e) {}
    ({ ws, cdp } = await connect());
    try {
      const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
      const safe = r.name.replace(/[\\/:*?"<>|\s]/g, '_');
      const file = path.join(outDir, safe + '.png');
      fs.writeFileSync(file, Buffer.from(shot.data, 'base64'));
      console.log('SHOT ' + r.name + ' -> ' + file);
    } catch (e) {
      console.log('FAIL ' + r.name + ' : ' + e.message);
    }
  }
  try { ws.sock.destroy(); } catch (e) {}
}
main().catch(e => { console.error('FATAL', e.message); process.exit(1); });
