(() => {
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const out = {};

  // "更多"面板里的分组：每个 sidebarItem.cursor 是一个二级菜单组
  const groups = Array.from(document.querySelectorAll('.sidebarItem.cursor'));
  out.groupCount = groups.length;
  out.groups = groups.map(g => {
    const html = g.innerHTML.replace(/\s+/g, ' ');
    // 提取该组内的子项（通常有独立的 class）
    const kids = Array.from(g.querySelectorAll('*'))
      .filter(e => e.children.length === 0 && norm(e.innerText))
      .map(e => ({ t: norm(e.innerText).slice(0, 20), cls: (e.className || '').toString().slice(0, 50) }));
    const uniq = [];
    kids.forEach(k => { if (!uniq.some(u => u.t === k.t)) uniq.push(k); });
    return {
      title: norm(g.innerText).slice(0, 60),
      html: html.slice(0, 700),
      leaves: uniq.slice(0, 30),
    };
  });
  return JSON.stringify(out, null, 1);
})()
