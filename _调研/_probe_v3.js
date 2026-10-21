/**
 * Batch page probe v3 — full-page navigation (most reliable).
 * For each route: location.href = full URL, wait for load + content, then read state.
 */
const http = require('http'), net = require('net'), crypto = require('crypto'), fs = require('fs');
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
    this.sock.on('data', ch => {
      this.buf = Buffer.concat([this.buf, ch]);
      if (!hs) { const i = this.buf.indexOf('\r\n\r\n'); if (i < 0) return;
        if (!/101/.test(this.buf.slice(0, i).toString())) return reject(new Error('handshake'));
        this.buf = this.buf.slice(i + 4); hs = true; resolve(); }
      this.drain();
    });
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
      setTimeout(() => { if (this.p.has(id)) { this.p.delete(id); rej(new Error('timeout ' + method)); } }, 120000); }); }
  async eval(e, ap = false) { const r = await this.send('Runtime.evaluate',
    { expression: e, returnByValue: true, awaitPromise: ap, userGesture: true, allowUnsafeEvalBlockedByCSP: true });
    if (r.exceptionDetails) throw new Error('JS: ' + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
    return r.result.value; }
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

const READ_FALLBACK = `(() => {
  const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
  const o = { url: location.href, title: document.title };
  o.hasTableDom = !!document.querySelector('.ant-table');
  o.hasTree = !!document.querySelector('.ant-tree, .ant-tree-list');
  o.hasCanvas = document.querySelectorAll('canvas').length;
  o.hasCard = document.querySelectorAll('.ant-card').length;
  o.hasDescriptions = !!document.querySelector('.ant-descriptions');
  o.hasTabs = !!document.querySelector('.ant-tabs');
  o.tableRows = document.querySelectorAll('.ant-table-tbody tr.ant-table-row').length;
  const pg = document.querySelector('.ant-pagination');
  o.pagination = pg ? norm(pg.innerText).slice(0, 110) : null;
  const em = document.querySelector('.ant-empty-description');
  o.empty = em ? norm(em.innerText) : null;
  o.headers = Array.from(document.querySelectorAll('.ant-table thead th')).map(t => norm(t.innerText)).filter(Boolean).slice(0, 28);
  const f = document.querySelector('.ant-table-tbody tr.ant-table-row');
  if (f) o.sample = Array.from(f.querySelectorAll('td')).map(td => norm(td.innerText).slice(0, 18)).slice(0, 10);
  o.forms = Array.from(document.querySelectorAll('.ant-form-item-label label')).map(l => norm(l.innerText)).filter(Boolean).slice(0, 26);
  o.buttons = [...new Set(Array.from(document.querySelectorAll('.ant-btn')).map(b => norm(b.innerText)).filter(Boolean))].slice(0, 22);
  const c = document.querySelector('.ant-layout-content') || document.body;
  o.contentText = norm(c.innerText).slice(0, 1500);
  return JSON.stringify(o);
})()`;

async function main() {
  const routes = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const outFile = process.argv[3];
  const READ = process.argv[4] && fs.existsSync(process.argv[4])
    ? fs.readFileSync(process.argv[4], 'utf8')
    : READ_FALLBACK;
  const results = fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile, 'utf8')) : [];
  const done = new Set(results.map(r => r.route));

  let { ws, cdp } = await connect();
  let sinceReconnect = 0;

  for (const r of routes) {
    if (done.has(r.route)) { console.log('skip (done) ' + r.name); continue; }
    const full = r.route.startsWith('http') ? r.route : BASE + r.route;
    try {
      await cdp.eval(`location.href = ${JSON.stringify(full)}; 'go'`, false);
    } catch (e) { /* navigation kills the context — expected */ }
    await new Promise(res => setTimeout(res, 5200));
    // reconnect after each navigation (execution context replaced)
    try { ws.sock.destroy(); } catch (e) {}
    ({ ws, cdp } = await connect());
    try {
      const o = JSON.parse(await cdp.eval(READ, false));
      o.name = r.name; o.group = r.group; o.route = r.route;
      results.push(o);
      const v = o.pagination ? o.pagination
        : o.empty ? 'EMPTY:' + o.empty
        : o.tableRows ? o.tableRows + ' rows'
        : o.hasCanvas ? 'canvas x' + o.hasCanvas
        : o.hasTree ? 'TREE'
        : o.contentText ? 'text:' + o.contentText.slice(0, 70)
        : 'BLANK';
      console.log(`${r.group} / ${r.name}  ->  ${v}`);
    } catch (e) {
      results.push({ group: r.group, name: r.name, route: r.route, error: e.message });
      console.log(`${r.group} / ${r.name}  ->  ERR ${e.message}`);
    }
    fs.writeFileSync(outFile, JSON.stringify(results, null, 1), 'utf8');
  }
  console.log('\nsaved ' + outFile + ' (' + results.length + ')');
  try { ws.sock.destroy(); } catch (e) {}
}
main().catch(e => { console.error('FATAL', e.message); process.exit(1); });
