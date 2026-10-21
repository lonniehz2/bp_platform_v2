(() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = {};

  // 找到侧边栏容器
  const sidebar = document.querySelector('[class*="sidebar"]') || document.querySelector('aside') || document.body;
  out.sidebarClass = (sidebar.className || '').toString().slice(0, 150);

  // 所有含"菜单组"特征的元素
  const groups = Array.from(document.querySelectorAll('[class*="sidebar"]'))
    .filter(e => {
      const t = norm(e.innerText);
      return t && t.length > 10 && t.length < 600 && e.querySelectorAll('[class*="sidebar"]').length <= 3;
    })
    .slice(0, 12);
  out.groupCount = groups.length;
  out.groups = groups.map(e => ({ cls: (e.className||'').toString().slice(0,80), text: norm(e.innerText).slice(0, 500) }));

  // 直接取「更多」菜单的 innerHTML 结构（它含全部二级菜单）
  const more = document.querySelector('.more_item_menu');
  if (more) {
    out.moreHtml = more.innerHTML.replace(/\s+/g, ' ').slice(0, 4000);
  }

  // 列出所有 class 名里含 menu / sidebar 的元素及其文本
  const seen = new Set();
  const menuEls = [];
  Array.from(document.querySelectorAll('*')).forEach(e => {
    const c = (e.className || '').toString();
    if (!/menu|sidebar|nav/i.test(c)) return;
    const t = norm(e.innerText);
    if (!t || t.length > 300) return;
    const key = c + '|' + t.slice(0, 60);
    if (seen.has(key)) return;
    seen.add(key);
    menuEls.push({ cls: c.slice(0, 90), text: t.slice(0, 200), kids: e.children.length });
  });
  out.menuEls = menuEls.slice(0, 60);

  return JSON.stringify(out, null, 1);
})()
