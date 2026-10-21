(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href };

  // 1) 顶部一级导航
  const topSel = ['.ant-menu-horizontal', 'header', '.layout-header', 'nav'];
  let top = [];
  for (const sel of topSel) {
    const el = document.querySelector(sel);
    if (el) {
      const t = norm(el.innerText);
      if (t) { top.push({ sel, text: t.slice(0, 600) }); }
    }
  }
  out.topNav = top;

  // 2) 左侧菜单（如有）
  const sideEl = document.querySelector('.ant-menu-vertical, .ant-menu-inline, aside .ant-menu, .layout-sider .ant-menu');
  out.sideMenu = sideEl ? norm(sideEl.innerText).slice(0, 3000) : null;

  // 3) 所有菜单项（含隐藏）
  const items = Array.from(document.querySelectorAll('.ant-menu-item, .ant-menu-submenu-title'))
    .map(e => norm(e.innerText)).filter(Boolean);
  out.menuItems = [...new Set(items)].slice(0, 200);

  // 4) 路由表（前端可能暴露）
  out.routes = null;

  // 5) 页面结构线索
  out.cards = Array.from(document.querySelectorAll('.ant-card-head-title')).map(e => norm(e.innerText)).filter(Boolean).slice(0, 40);

  return JSON.stringify(out, null, 1);
})()
