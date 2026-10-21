(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const want = process.env.YM_MENU || '';
  const out = { want, urlBefore: location.href };

  // 1) 悬停"更多"展开面板
  const more = Array.from(document.querySelectorAll('.sidebarItem'))
    .find(e => norm(e.innerText).slice(0, 10) === '更多');
  if (more) {
    const nm = more.querySelector('.menuName') || more;
    nm.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
    nm.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    nm.click();
    await sleep(1500);
  }

  // 2) 在展开的面板里点目标
  const panel = document.querySelector('.more_item_menu');
  out.panelRect = panel ? (r => ({ x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }))(panel.getBoundingClientRect()) : null;

  // 搜索整个文档里文本等于 want 的可点击叶子
  const cands = Array.from(document.querySelectorAll('div,span,a,li'))
    .filter(e => norm(e.innerText) === want && e.getBoundingClientRect().width > 10);
  out.found = cands.length;
  if (cands.length) {
    const t = cands[0];
    const r = t.getBoundingClientRect();
    out.targetRect = { x: Math.round(r.x), y: Math.round(r.y) };
    t.click();
    await sleep(4000);
  }
  out.urlAfter = location.href;
  out.title = document.title;
  out.text = document.body.innerText.slice(0, 900);
  return JSON.stringify(out, null, 1);
})()
