const fs = require('fs');
const rows = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const num = s => { if (!s) return null; const m = String(s).match(/([\d,]+)/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; };
const out = [];
for (const r of rows) {
  const blank = !r.pagination && !r.empty && !r.tableRows && !r.hasCanvas && !r.hasTree &&
    !(r.contentText && r.contentText.length > 40);
  if (blank) out.push({ group: r.group, name: r.name, route: r.route });
}
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1), 'utf8');
console.log('blank pages to re-probe with polling: ' + out.length);
out.forEach(o => console.log('  ' + o.name + '  ' + o.route));
