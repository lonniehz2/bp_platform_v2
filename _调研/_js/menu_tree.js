(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();

  // 1) 顶级菜单
  const tops = Array.from(document.querySelectorAll('li.ant-menu-item, li.ant-menu-submenu'))
    .filter(el => el.closest('.ant-menu-root'))
    .map(el => {
      const isSub = el.classList.contains('ant-menu-submenu');
      const titleEl = isSub ? el.querySelector(':scope > .ant-menu-submenu-title') : el;
      return { name: norm(titleEl && titleEl.innerText), isSubmenu: isSub, el };
    })
    .filter(x => x.name);

  const result = [];

  // 2) 逐个展开并抓子项
  for (const t of tops) {
    if (!t.isSubmenu) { result.push({ name: t.name, children: [] }); continue; }
    const titleEl = t.el.querySelector(':scope > .ant-menu-submenu-title');
    const opened = t.el.classList.contains('ant-menu-submenu-open');
    if (!opened) {
      titleEl.click();
      await sleep(320);
    }
    const kids = Array.from(t.el.querySelectorAll('.ant-menu-sub > li.ant-menu-item, .ant-menu-sub li.ant-menu-item'))
      .map(k => norm(k.innerText)).filter(Boolean);
    result.push({ name: t.name, children: kids });
    if (!opened) { titleEl.click(); await sleep(160); }
  }

  return JSON.stringify(result, null, 1);
})()
