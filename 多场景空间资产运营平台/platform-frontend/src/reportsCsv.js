export function buildCsv(header, rows) {
  const lines = [header, ...rows].map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(','))
  return '\ufeff' + lines.join('\n')
}
