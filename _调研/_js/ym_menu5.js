(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href, menus: [] };

  const tops = Array.from(document.querySelectorAll('.sidebarItemBox'));
  out.topCount = tops.length;

  for (const el of tops) {
    const nmEl = el.querySelector('.menuName');
    const name = norm(nmEl ? nmEl.innerText : el.innerText).slice(0, 30);
    const clickable = nmEl || el;
    clickable.click();
    await sleep(800);

    // 只扫描侧边栏区域，且不调 getComputedStyle
    const seen = new Set();
    const items = [];
    const nodes = document.querySelectorAll('div,span,a,li,p');
    for (let i = 0; i < nodes.length; i++) {
      const e = nodes[i];
      const t = norm(e.innerText);
      if (!t || t.length > 18) continue;
      if (/^(仪表盘|线索|房源|合同|财务|管理后台|更多)$/.test(t)) continue;
      const childText = norm(Array.from(e.children).map(c => c.innerText).join(''));
      if (childText === t) continue;          // 非叶子
      const r = e.getBoundingClientRect();
      if (r.width < 10 || r.height < 10) continue;
      if (r.left > 420 || r.top > 1000 || r.top < 0) continue;   // 只看左侧区域
      if (seen.has(t)) continue;
      seen.add(t);
      items.push({ t, y: Math.round(r.top), x: Math.round(r.left) });
    }
    items.sort((a, b) => a.y - b.y);
    out.menus.push({ name, items: items.map(i => i.t) });
  }
  return JSON.stringify(out, null, 1);
})()
