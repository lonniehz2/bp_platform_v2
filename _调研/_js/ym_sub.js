(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const target = process.env.YM_MENU || '';
  const out = { target, urlBefore: location.href, sub: [] };

  const tops = Array.from(document.querySelectorAll('.sidebarItem'))
    .filter(e => /show_menu_item|sidebarActive|more_item_menu/.test((e.className || '').toString()));
  const el = tops.find(e => norm(e.innerText).slice(0, 10) === target);
  if (!el) return JSON.stringify({ ...out, err: 'not found', tops: tops.map(e => norm(e.innerText).slice(0, 10)) });

  (el.querySelector('.menuName') || el).click();
  await sleep(1600);
  out.urlAfter = location.href;

  // 一级菜单的二级项就是 .menu-item-text（在顶部标签栏 y≈19）
  const items = Array.from(document.querySelectorAll('.menu-item-text'));
  out.sub = items.map(e => {
    const r = e.getBoundingClientRect();
    return { t: norm(e.innerText).slice(0, 20), x: Math.round(r.left), active: /itemHigh/.test((e.className || '').toString()) };
  }).filter(x => x.t).sort((a, b) => a.x - b.x);

  return JSON.stringify(out, null, 1);
})()
