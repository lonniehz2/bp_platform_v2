(() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href, title: document.title };

  // 侧边栏容器里所有 sidebarItem（一级菜单项）
  const items = Array.from(document.querySelectorAll('.sidebarItem'));
  out.sidebarItems = items.map(e => ({
    cls: (e.className || '').toString().slice(0, 90),
    text: norm(e.innerText).slice(0, 60),
    left: Math.round(e.getBoundingClientRect().left),
    top: Math.round(e.getBoundingClientRect().top),
  }));

  // 顶部页签区域（当前"房源"下的子菜单就出现在顶部）
  const header = document.querySelector('header') || document.querySelector('[class*="header"]');
  out.headerText = header ? norm(header.innerText).slice(0, 800) : null;

  // 找所有含"独栋/合整租"等页签特征的元素
  const tabs = Array.from(document.querySelectorAll('[class*="tab"],[class*="Tab"],[class*="nav"],[class*="Nav"]'))
    .map(e => ({ cls: (e.className || '').toString().slice(0, 70), text: norm(e.innerText).slice(0, 200) }))
    .filter(x => x.text && x.text.length < 300)
    .slice(0, 20);
  out.tabs = tabs;

  return JSON.stringify(out, null, 1);
})()
