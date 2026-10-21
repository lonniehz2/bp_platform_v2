(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || '').replace(/\s+/g, ' ').trim();

  // 点击"住房申请"标签
  const all = Array.from(document.querySelectorAll('div,span,a,li'));
  const tab = all.find(e => norm(e.innerText) === '住房申请' && e.getBoundingClientRect().top < 120);
  if (tab) { tab.click(); await sleep(3500); }

  const out = {
    url: location.href,
    title: document.title,
    // 页面上所有表头（列名）——最能反映业务字段
    tableHeaders: [],
    // 表单字段
    formLabels: [],
    // 按钮
    buttons: [],
    // 顶部标签
    tabs: [],
    text: document.body.innerText.slice(0, 2500),
  };

  document.querySelectorAll('th, .ant-table-cell').forEach(e => {
    const t = norm(e.innerText);
    if (t && t.length < 20 && !out.tableHeaders.includes(t)) out.tableHeaders.push(t);
  });
  document.querySelectorAll('label, .ant-form-item-label').forEach(e => {
    const t = norm(e.innerText);
    if (t && t.length < 24 && !out.formLabels.includes(t)) out.formLabels.push(t);
  });
  document.querySelectorAll('button').forEach(e => {
    const t = norm(e.innerText);
    if (t && t.length < 20 && !out.buttons.includes(t)) out.buttons.push(t);
  });
  all.forEach(e => {
    const r = e.getBoundingClientRect();
    if (r.top > 120 || r.left < 70 || r.width < 12) return;
    const t = norm(e.innerText);
    if (t && t.length < 14 && !out.tabs.includes(t)) out.tabs.push(t);
  });

  return JSON.stringify(out, null, 1);
})()
