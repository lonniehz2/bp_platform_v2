(() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = { url: location.href };

  // 找出包含「线索/房源/合同/财务」文本的元素及其选择器特征
  const targets = ['线索', '房源', '合同', '财务', '管理后台', '更多'];
  const hits = [];
  targets.forEach(t => {
    const all = Array.from(document.querySelectorAll('*')).filter(e => {
      const own = norm(Array.from(e.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join(''));
      return own === t;
    });
    hits.push({ text: t, count: all.length, samples: all.slice(0, 3).map(e => ({
      tag: e.tagName,
      cls: (e.className || '').toString().slice(0, 120),
      parentCls: (e.parentElement && e.parentElement.className || '').toString().slice(0, 120),
      href: e.closest('a') ? e.closest('a').getAttribute('href') : null,
    }))});
  });
  out.menuHits = hits;

  // 打印第一层布局结构（深度 4）
  function tree(el, depth, maxDepth, acc) {
    if (!el || depth > maxDepth) return;
    const cls = (el.className || '').toString().split(' ').filter(Boolean).slice(0, 4).join('.');
    const txt = norm(el.innerText || '').slice(0, 40);
    acc.push('  '.repeat(depth) + el.tagName.toLowerCase() + (cls ? '.' + cls : '') + (txt ? '  | ' + txt : ''));
    Array.from(el.children).slice(0, 6).forEach(c => tree(c, depth + 1, maxDepth, acc));
  }
  const body = document.body;
  const acc = [];
  tree(body, 0, 3, acc);
  out.domTree = acc.slice(0, 80);

  // 所有链接
  out.links = Array.from(document.querySelectorAll('a[href]')).map(a => ({
    t: norm(a.innerText).slice(0, 24), h: a.getAttribute('href')
  })).filter(x => x.t || x.h).slice(0, 60);

  return JSON.stringify(out, null, 1);
})()
