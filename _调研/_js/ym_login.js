(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const setVal = (el, val) => {
    const d = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
    d.set.call(el, val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
  };

  const u = document.querySelector('input[name="username"]');
  const p = document.querySelector('input[name="password"]');
  if (!u || !p) return JSON.stringify({ ok: false, err: 'fields not found' });

  u.focus(); setVal(u, '17701311856'); await sleep(300);
  p.focus(); setVal(p, 'a123456'); await sleep(300);

  const btn = Array.from(document.querySelectorAll('button')).find(b => /登\s*录/.test(b.innerText));
  if (!btn) return JSON.stringify({ ok: false, err: 'login button not found' });
  btn.click();

  await sleep(6000);
  return JSON.stringify({
    ok: true,
    url: location.href,
    title: document.title,
    loggedIn: !/login/.test(location.href),
    text: document.body.innerText.slice(0, 600),
    uVal: u.value, pVal: (p.value || '').length,
  }, null, 1);
})()
