/** 金额/数字展示工具：千分位 + 两位小数。 */

export function fmtMoney(v, dash = '0.00') {
  if (v === null || v === undefined || v === '') return dash
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function fmtQty(v, dash = '—') {
  if (v === null || v === undefined || v === '') return dash
  const n = Number(v)
  if (Number.isNaN(n)) return String(v)
  return n.toLocaleString('zh-CN', { maximumFractionDigits: 4 })
}
