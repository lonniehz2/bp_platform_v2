(() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href, title: document.title };

  // 结构化扫描：找出所有"菜单叶节点"
  const cands = [];
  document.querySelectorAll('*').forEach(e => {
    const c = (e.className || '').toString();
    if (!/menuName|sidebarItem|mouse-hover-bg|menu-item|submenu/i.test(c)) return;
    const t = norm(e.innerText);
    if (!t || t.length > 30) return;
    cands.push({
      cls: c.slice(0, 70),
      text: t,
      depth: (() => { let d = 0, p = e; while (p && p.parentElement) { d++; p = p.parentElement; } return d; })(),
      tag: e.tagName,
    });
  });
  out.leafCount = cands.length;
  out.leaves = cands.slice(0, 200);

  // 侧边栏最外层
  const sb = document.querySelector('.sidebarItemBox');
  out.sidebarHtml = sb && sb.parentElement ? sb.parentElement.outerHTML.replace(/\s+/g, ' ').slice(0, 6000) : null;

  return JSON.stringify(out, null, 1);
})()
