(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const target = process.env.YM_MENU || '';
  const out = { target, urlBefore: location.href };

  const tops = Array.from(document.querySelectorAll('.sidebarItem'))
    .filter(e => /show_menu_item|sidebarActive|more_item_menu/.test((e.className || '').toString()));
  out.topNames = tops.map(e => norm(e.innerText).slice(0, 20));

  const el = tops.find(e => {
    const n = e.querySelector('.menuName');
    return norm(n ? n.innerText : e.innerText).slice(0, 20) === target;
  });
  if (!el) return JSON.stringify({ ...out, err: 'menu not found' });

  (el.querySelector('.menuName') || el).click();
  await sleep(1500);
  out.urlAfter = location.href;

  // 只扫描顶部区域内的少量候选（用 querySelectorAll 限定范围，快）
  const cand = [];
  const nodes = document.querySelectorAll('div,span,a,li');
  for (let i = 0; i < nodes.length; i++) {
    const e = nodes[i];
    const r = e.getBoundingClientRect();
    if (r.top > 120 || r.left < 70 || r.width < 12 || r.height < 12) continue;   // 先做几何过滤（便宜）
    const t = norm(e.innerText);
    if (!t || t.length > 14) continue;
    const childTxt = norm(Array.from(e.children).map(c => c.innerText).join(''));
    if (childTxt === t) continue;
    if (cand.some(c => c.t === t)) continue;
    cand.push({ t, x: Math.round(r.left), y: Math.round(r.top) });
  }
  cand.sort((a, b) => a.x - b.x || a.y - b.y);
  out.tabs = cand.map(c => c.t);
  return JSON.stringify(out, null, 1);
})()
