(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href };

  // 所有 sidebarItemBox（一级菜单）
  const tops = Array.from(document.querySelectorAll('.sidebarItemBox'));
  out.topCount = tops.length;
  out.topMenus = tops.map(e => norm(e.innerText).slice(0, 60));

  // 逐个 hover/点击展开，抓子菜单
  const tree = [];
  for (const el of tops) {
    const name = norm(el.innerText).slice(0, 40);
    // 尝试 hover 触发子菜单
    el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    const clickable = el.querySelector('.menuName') || el;
    clickable.click();
    await sleep(700);

    // 展开后的面板：查找弹出层里的菜单项
    const panels = Array.from(document.querySelectorAll(
      '.sidebarItem, .more_item_menu, .subMenuItem, [class*="subMenu"], [class*="sub-menu"], .ant-menu-item'
    ));
    const kids = [];
    panels.forEach(p => {
      if (el.contains(p)) return;
      const t = norm(p.innerText);
      if (t && t.length < 40 && !kids.includes(t)) kids.push(t);
    });
    tree.push({ name, children: kids.slice(0, 60) });
  }
  out.tree = tree;

  return JSON.stringify(out, null, 1);
})()
