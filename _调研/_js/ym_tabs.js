(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href, menus: [] };

  const tops = Array.from(document.querySelectorAll('.sidebarItem'))
    .filter(e => /show_menu_item|sidebarActive|more_item_menu/.test((e.className || '').toString()));
  out.topNames = tops.map(e => norm(e.innerText).slice(0, 20));

  for (const el of tops) {
    const nmEl = el.querySelector('.menuName');
    const name = norm(nmEl ? nmEl.innerText : el.innerText).slice(0, 20);
    if (!name) continue;
    const clickable = nmEl || el;
    clickable.click();
    await sleep(1200);

    // 顶部子标签：位于页面顶部、短的、横向排列的文本
    const cand = [];
    const nodes = document.querySelectorAll('div,span,a,li');
    for (let i = 0; i < nodes.length; i++) {
      const e = nodes[i];
      const t = norm(e.innerText);
      if (!t || t.length > 14) continue;
      const childTxt = norm(Array.from(e.children).map(c => c.innerText).join(''));
      if (childTxt === t) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 12 || r.height < 12) continue;
      if (r.top > 110 || r.left < 70) continue;      // 顶部标签栏区域
      if (cand.some(c => c.t === t)) continue;
      cand.push({ t, x: Math.round(r.left), y: Math.round(r.top) });
    }
    cand.sort((a, b) => a.x - b.x);
    out.menus.push({ name, tabs: cand.map(c => c.t) });
  }
  return JSON.stringify(out, null, 1);
})()
