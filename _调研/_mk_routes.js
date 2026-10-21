// Build routes.json from menu_routes.json (actual sidebar routes)
const fs = require('fs');
const src = JSON.parse(fs.readFileSync(process.argv[2], 'utf8').replace(/^\uFEFF/, ''));
const out = [];
const seen = new Set();
for (const g of src) {
  if (g.route) {
    if (!seen.has(g.route)) { seen.add(g.route); out.push({ group: g.group, name: g.group, route: g.route }); }
  }
  for (const c of (g.children || [])) {
    if (!c.route || seen.has(c.route)) continue;
    seen.add(c.route);
    out.push({ group: g.group, name: c.name, route: c.route });
  }
}
// skip the tab-context-menu pseudo entries
const filtered = out.filter(r => r.route && !/^(刷新|关闭)/.test(r.name));
fs.writeFileSync(process.argv[3], JSON.stringify(filtered, null, 1), 'utf8');
console.log('routes: ' + filtered.length);
filtered.forEach(r => console.log('  ' + r.group + ' / ' + r.name + '  ' + r.route));
