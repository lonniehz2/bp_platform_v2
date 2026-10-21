(async () => {
  const out = { url: location.href };
  try {
    const sleep = ms => new Promise(r => setTimeout(r, ms));
    const norm = s => (s || '').replace(/\s+/g, ' ').trim();
    const t0 = Date.now();

    // 每次评估最多等 ~15s，绝不触发 CDP 侧超时
    const deadline = 15000;
    let last = '';
    while (Date.now() - t0 < deadline) {
      await sleep(400);
      const c = document.querySelector('.ant-layout-content') || document.body;
      const txt = norm(c.innerText);
      if (document.querySelector('.ant-table-tbody tr.ant-table-row, .ant-empty-description, .ant-tree, .ant-descriptions, .ant-statistic, canvas')) break;
      if (txt.length > 60 && txt === last) break;   // 内容已稳定
      last = txt;
    }
    await sleep(900);
    out.elapsedMs = Date.now() - t0;

    out.hasTableDom = !!document.querySelector('.ant-table');
    out.hasTree = !!document.querySelector('.ant-tree, .ant-tree-list');
    out.hasCanvas = document.querySelectorAll('canvas').length;
    out.hasDescriptions = !!document.querySelector('.ant-descriptions');
    out.hasTabs = !!document.querySelector('.ant-tabs');
    out.tableRows = document.querySelectorAll('.ant-table-tbody tr.ant-table-row').length;
    const pg = document.querySelector('.ant-pagination');
    out.pagination = pg ? norm(pg.innerText).slice(0, 110) : null;
    const em = document.querySelector('.ant-empty-description');
    out.empty = em ? norm(em.innerText) : null;
    out.headers = Array.from(document.querySelectorAll('.ant-table thead th')).map(t => norm(t.innerText)).filter(Boolean).slice(0, 30);
    const f = document.querySelector('.ant-table-tbody tr.ant-table-row');
    if (f) out.sample = Array.from(f.querySelectorAll('td')).map(td => norm(td.innerText).slice(0, 18)).slice(0, 12);
    out.forms = Array.from(document.querySelectorAll('.ant-form-item-label label')).map(l => norm(l.innerText)).filter(Boolean).slice(0, 26);
    out.buttons = [...new Set(Array.from(document.querySelectorAll('.ant-btn')).map(b => norm(b.innerText)).filter(Boolean))].slice(0, 22);
    const c2 = document.querySelector('.ant-layout-content') || document.body;
    out.contentText = norm(c2.innerText).slice(0, 1200);
    out.contentHtmlLen = c2.innerHTML.length;
    out.ok = true;
  } catch (e) {
    out.ok = false;
    out.err = String((e && e.message) || e);
  }
  return JSON.stringify(out);
})()
