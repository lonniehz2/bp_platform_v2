(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href, menus: [] };

  const tops = Array.from(document.querySelectorAll('.sidebarItemBox'));
  for (const el of tops) {
    const name = norm(el.querySelector('.menuName') ? el.querySelector('.menuName').innerText : el.innerText).slice(0, 30);

    // 点击展开
    const clickable = el.querySelector('.menuName') || el;
    clickable.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    clickable.click();
    await sleep(900);

    // 展开后：所有可见的、深度较深的小文本节点（菜单项特征：短文本 + 可点击）
    const seen = new Set();
    const items = [];
    document.querySelectorAll('div,span,a,li,p').forEach(e => {
      const t = norm(e.innerText);
      if (!t || t.length > 16) return;           // 菜单项通常很短
      if (t === name) return;
      if (/^(仪表盘|线索|房源|合同|财务|管理后台|更多)$/.test(t)) return;
      const st = getComputedStyle(e);
      if (st.display === 'none' || st.visibility === 'hidden') return;
      const r = e.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) return;
      // 只要没有子元素里的文本（叶子）
      const childText = norm(Array.from(e.children).map(c => c.innerText).join(''));
      if (childText === t) return;
      if (seen.has(t)) return;
      seen.add(t);
      items.push({ t, cls: (e.className || '').toString().slice(0, 60), y: Math.round(r.top), x: Math.round(r.left) });
    });

    // 按位置排序（y 优先），过滤掉工作台正文里的短文本
    const leftItems = items.filter(i => i.x < 400);
    leftItems.sort((a, b) => a.y - b.y);
    out.menus.push({ name, items: leftItems.map(i => i.t) });
  }
  return JSON.stringify(out, null, 1);
})()
