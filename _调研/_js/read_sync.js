(() => {
  const out = { url: location.href, t: Date.now() };
  try {
    const norm = s => (s || '').replace(/\s+/g, ' ').trim();
    out.hasTableDom = !!document.querySelector('.ant-table');
    out.hasTree = !!document.querySelector('.ant-tree, .ant-tree-list');
    out.hasCanvas = document.querySelectorAll('canvas').length;
    out.hasDescriptions = !!document.querySelector('.ant-descriptions');
    out.hasTabs = !!document.querySelector('.ant-tabs');
    out.hasSpin = document.querySelectorAll('.ant-spin-spinning').length;
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
    const c = document.querySelector('.ant-layout-content') || document.body;
    out.contentText = norm(c.innerText).slice(0, 1500);
    out.contentHtmlLen = c.innerHTML.length;
    out.ok = true;
  } catch (e) {
    out.ok = false;
    out.err = String((e && e.message) || e);
  }
  return JSON.stringify(out);
})()
