(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = {};

  // 1) "更多"面板是否已展开（覆盖页面）
  const more = document.querySelector('.more_item_menu');
  if (more) {
    const r = more.getBoundingClientRect();
    out.morePanel = {
      rect: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
      visible: r.width > 0 && r.height > 0,
    };
    // 面板内所有可点击项（子菜单）
    const panelItems = Array.from(more.querySelectorAll('*'))
      .filter(e => {
        const t = norm(e.innerText);
        if (!t || t.length > 20) return false;
        const kids = norm(Array.from(e.children).map(c => c.innerText).join(''));
        if (kids === t) return false;                      // 叶子
        const rr = e.getBoundingClientRect();
        return rr.width > 4 && rr.height > 4;
      })
      .map(e => {
        const rr = e.getBoundingClientRect();
        return { t: norm(e.innerText).slice(0, 20), cls: (e.className || '').toString().slice(0, 50), y: Math.round(rr.top), x: Math.round(rr.left) };
      });
    const uniq = [];
    panelItems.forEach(p => { if (!uniq.some(u => u.t === p.t)) uniq.push(p); });
    uniq.sort((a, b) => a.x - b.x || a.y - b.y);
    out.moreItems = uniq.slice(0, 80);
  } else {
    out.morePanel = null;
  }

  // 2) 顶部标签的真实容器（一级菜单对应）
  // 先点一下"房源"，再看顶部标签
  const tops = Array.from(document.querySelectorAll('.sidebarItem'))
    .filter(e => /show_menu_item|sidebarActive/.test((e.className || '').toString()));
  const fangyuan = tops.find(e => norm(e.innerText).slice(0, 10) === '房源');
  if (fangyuan) { (fangyuan.querySelector('.menuName') || fangyuan).click(); await sleep(1800); }

  out.urlAfterFangyuan = location.href;

  // 顶部标签容器：找出所有 y<120 且是"兄弟并列"的元素
  const cand = [];
  const nodes = document.querySelectorAll('div,span,a,li');
  for (let i = 0; i < nodes.length; i++) {
    const e = nodes[i];
    const r = e.getBoundingClientRect();
    if (r.top > 118 || r.left < 70 || r.width < 12 || r.height < 12) continue;
    const t = norm(e.innerText);
    if (!t || t.length > 16) continue;
    const kids = norm(Array.from(e.children).map(c => c.innerText).join(''));
    if (kids === t) continue;
    if (cand.some(c => c.t === t)) continue;
    cand.push({ t, x: Math.round(r.left), y: Math.round(r.top), cls: (e.className || '').toString().slice(0, 45) });
  }
  cand.sort((a, b) => a.x - b.x || a.y - b.y);
  out.topTabs = cand.slice(0, 40);

  return JSON.stringify(out, null, 1);
})()
