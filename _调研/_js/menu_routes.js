(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const menuRoot = document.querySelector('ul.ant-menu-root') || document.querySelector('.ant-menu');
  const tops = Array.from(menuRoot.querySelectorAll(':scope > li.ant-menu-item, :scope > li.ant-menu-submenu'));
  const out = [];
  for (const li of tops) {
    const isSub = li.classList.contains('ant-menu-submenu');
    if (!isSub) {
      const a = li.querySelector('a');
      out.push({ group: norm(li.innerText), route: a ? a.getAttribute('href') : null, children: [] });
      continue;
    }
    const title = li.querySelector(':scope > .ant-menu-submenu-title');
    const gname = norm(title.innerText);
    const wasOpen = li.classList.contains('ant-menu-submenu-open');
    if (!wasOpen) { title.click(); await sleep(350); }
    const kids = Array.from(li.querySelectorAll('li.ant-menu-item')).map(k => {
      const a = k.querySelector('a');
      return { name: norm(k.innerText), route: a ? a.getAttribute('href') : null };
    }).filter(k => k.name);
    out.push({ group: gname, route: null, children: kids });
    if (!wasOpen) { title.click(); await sleep(150); }
  }
  return JSON.stringify(out, null, 1);
})()
