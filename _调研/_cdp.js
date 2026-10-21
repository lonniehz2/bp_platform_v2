// 复用已登录页面（修正版：不使用 keep-alive，显式退出）
const http = require('http'), net = require('net'), crypto = require('crypto'), fs = require('fs');
const PORT = process.env.CDP_PORT || 9334;
const MATCH = process.env.CDP_MATCH || 'saas.yumeng.work';

const httpGet = p => new Promise((res, rej) => {
  const req = http.request({ host: '127.0.0.1', port: PORT, path: p, agent: false }, r => {
    let d = ''; r.setEncoding('utf8');
    r.on('data', c => d += c); r.on('end', () => res(d));
  });
  req.on('error', rej);
  req.setTimeout(15000, () => { req.destroy(new Error('http timeout')); });
  req.end();
});

class WS {
  constructor(url) {
    const m = url.match(/^ws:\/\/([^:/]+):(\d+)(\/.*)$/);
    this.host = m[1]; this.port = +m[2]; this.path = m[3]; this.buf = Buffer.alloc(0); this.msg = () => {};
  }
  connect() {
    return new Promise((resolve, reject) => {
      const key = crypto.randomBytes(16).toString('base64');
      this.sock = net.connect(this.port, this.host, () =>
        this.sock.write(`GET ${this.path} HTTP/1.1\r\nHost: ${this.host}:${this.port}\r\n` +
          `Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: ${key}\r\n` +
          `Sec-WebSocket-Version: 13\r\n\r\n`));
      this.sock.setNoDelay(true);
      this.sock.on('error', reject);
      let hs = false;
      const onData = ch => {
        this.buf = Buffer.concat([this.buf, ch]);
        if (!hs) {
          const i = this.buf.indexOf('\r\n\r\n');
          if (i < 0) return;
          if (!/101/.test(this.buf.slice(0, i).toString())) return reject(new Error('hs fail'));
          this.buf = this.buf.slice(i + 4); hs = true;
          this.sock.removeListener('data', onData);
          this.sock.on('data', c => { this.buf = Buffer.concat([this.buf, c]); this.drain(); });
          this.drain(); resolve(); return;
        }
        this.drain();
      };
      this.sock.on('data', onData);
    });
  }
  drain() {
    for (;;) {
      if (this.buf.length < 2) return;
      const b1 = this.buf[1], op = this.buf[0] & 15, mk = (b1 & 128) !== 0;
      let len = b1 & 127, off = 2;
      if (len === 126) { if (this.buf.length < 4) return; len = this.buf.readUInt16BE(2); off = 4; }
      else if (len === 127) { if (this.buf.length < 10) return; len = Number(this.buf.readBigUInt64BE(2)); off = 10; }
      let k = null;
      if (mk) { if (this.buf.length < off + 4) return; k = this.buf.slice(off, off + 4); off += 4; }
      if (this.buf.length < off + len) return;
      let p = this.buf.slice(off, off + len);
      if (k) { p = Buffer.from(p); for (let i = 0; i < p.length; i++) p[i] ^= k[i % 4]; }
      this.buf = this.buf.slice(off + len);
      if (op === 1) { try { this.msg(JSON.parse(p.toString('utf8'))); } catch (e) {} }
      else if (op === 8) return;
      else if (op === 9) this.frame(p, 10);
    }
  }
  frame(pl, op = 1) {
    const d = Buffer.isBuffer(pl) ? pl : Buffer.from(pl, 'utf8');
    let h;
    if (d.length < 126) { h = Buffer.alloc(2); h[1] = 128 | d.length; }
    else if (d.length < 65536) { h = Buffer.alloc(4); h[1] = 128 | 126; h.writeUInt16BE(d.length, 2); }
    else { h = Buffer.alloc(10); h[1] = 128 | 127; h.writeBigUInt64BE(BigInt(d.length), 2); }
    h[0] = 128 | op;
    const k = crypto.randomBytes(4), m = Buffer.from(d);
    for (let i = 0; i < m.length; i++) m[i] ^= k[i % 4];
    this.sock.write(Buffer.concat([h, k, m]));
  }
  send(o) { this.frame(JSON.stringify(o)); }
}

class CDP {
  constructor(ws) {
    this.ws = ws; this.id = 0; this.p = new Map();
    ws.msg = m => {
      if (m.id && this.p.has(m.id)) {
        const { res, rej } = this.p.get(m.id); this.p.delete(m.id);
        m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
      }
    };
  }
  send(method, params = {}, timeout = 60000) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.p.set(id, { res, rej });
      this.ws.send({ id, method, params });
      const t = setTimeout(() => { if (this.p.has(id)) { this.p.delete(id); rej(new Error('timeout ' + method)); } }, timeout);
      if (t.unref) t.unref();
    });
  }
  async eval(expr, awaitPromise = false) {
    const r = await this.send('Runtime.evaluate', {
      expression: expr, returnByValue: true, awaitPromise,
      userGesture: true, allowUnsafeEvalBlockedByCSP: true,
    });
    if (r.exceptionDetails) {
      const d = r.exceptionDetails.exception;
      throw new Error('JS: ' + (d && (d.description || d.value) ? (d.description || d.value) : JSON.stringify(r.exceptionDetails)));
    }
    return r.result.value;
  }
}

async function attach() {
  const list = JSON.parse(await httpGet('/json/list'));
  const pages = list.filter(t => t.type === 'page' && t.url.includes(MATCH) && t.webSocketDebuggerUrl);
  const page = pages.find(t => !/\/login/.test(t.url)) || pages[0];
  if (!page) throw new Error('no matching page (CDP_MATCH=' + MATCH + ')');
  const ws = new WS(page.webSocketDebuggerUrl);
  await ws.connect();
  const cdp = new CDP(ws);
  await cdp.send('Runtime.enable');
  return { ws, cdp, page };
}

async function main() {
  const mode = process.argv[2], arg = process.argv[3];
  const { ws, cdp, page } = await attach();
  let code = 0;
  try {
    if (mode === 'js') {
      // 直接在源码里替换环境变量引用，不做包装（避免破坏脚本自身的 IIFE 结构）
      let src = fs.readFileSync(arg, 'utf8');
      src = src.replace(/process\.env\.YM_MENU/g, JSON.stringify(process.env.YM_MENU || ''))
               .replace(/process\.env\.YM_ARG/g, JSON.stringify(process.env.YM_ARG || ''));
      const v = await cdp.eval(src, true);
      console.log(typeof v === 'string' ? v : JSON.stringify(v, null, 1));
    } else if (mode === 'raw') {
      const v = await cdp.eval(arg, false);
      console.log(typeof v === 'string' ? v : JSON.stringify(v, null, 1));
    } else if (mode === 'shot') {
      const r = await cdp.send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(arg, Buffer.from(r.data, 'base64'));
      console.log('saved ' + arg + '   from ' + page.url);
    } else if (mode === 'list') {
      const list = JSON.parse(await httpGet('/json/list'));
      list.filter(t => t.type === 'page').forEach(t => console.log(t.url + '  ::  ' + t.title));
    } else if (mode === 'nav') {
      await cdp.eval(`location.href=${JSON.stringify(arg)}; 'go'`, false);
      console.log('nav -> ' + arg);
    } else { console.log('modes: js <file> | raw <expr> | shot <png> | list | nav <url>'); }
  } catch (e) { console.error('ERROR: ' + e.message); code = 1; }
  try { ws.sock.destroy(); } catch (e) {}
  process.exit(code);
}
main().catch(e => { console.error('FATAL: ' + e.message); process.exit(1); });
