(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  await sleep(1200);
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();
  const info = {
    url: location.href,
    title: document.title,
    tables: [],
    pagination: [],
    emptyHints: [],
    buttons: [],
    errorish: []
  };
  document.querySelectorAll('table').forEach((t, i) => {
    const heads = Array.from(t.querySelectorAll('thead th')).map(th => norm(th.innerText)).filter(Boolean);
    const rows = t.querySelectorAll('tbody tr');
    info.tables.push({ index: i, headers: heads.slice(0, 25), rowCount: rows.length });
  });
  document.querySelectorAll('.ant-pagination').forEach(p => {
    const total = p.querySelector('.ant-pagination-total-text');
    info.pagination.push(norm(total ? total.innerText : p.innerText).slice(0, 80));
  });
  document.querySelectorAll('.ant-empty, .ant-table-placeholder').forEach(e => {
    const t = norm(e.innerText);
    if (t) info.emptyHints.push(t.slice(0, 60));
  });
  document.querySelectorAll('button, .ant-btn').forEach(b => {
    const t = norm(b.innerText);
    if (t) info.buttons.push(t.slice(0, 20));
  });
  ['404', 'not found', '无权限', '错误', '找不到'].forEach(k => {
    if (document.body.innerText.includes(k)) info.errorish.push(k);
  });
  info.bodySnippet = norm(document.body.innerText).slice(0, 500);
  return JSON.stringify(info, null, 1);
})()
