/**
 * 通用 CSV 导出：带 BOM，Excel 打开中文不乱码。
 *
 * @param {string} filename 文件名（不含扩展名）
 * @param {Array<{key:string,label:string,map?:Function}>} columns 列定义
 * @param {Array<Object>} rows 数据行
 */
export function downloadCsv(filename, columns, rows) {
  const esc = (v) => {
    if (v === null || v === undefined) return ''
    const s = String(v).replace(/"/g, '""')
    return /[",\n\r]/.test(s) ? '"' + s + '"' : s
  }
  const header = columns.map((c) => esc(c.label)).join(',')
  const body = (rows || []).map((r) => columns.map((c) => {
    const raw = c.map ? c.map(r) : r[c.key]
    return esc(raw)
  }).join(','))
  const csv = '\ufeff' + [header].concat(body).join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename + '.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

/** 金额/日期空值统一显示为短横线 */
export function dash(v) {
  return v === null || v === undefined || v === '' ? '—' : v
}


/**
 * 分页拉取全量数据（后端单页上限 500）。
 * @param {Function} fetcher (params) => Promise<{rows,total}>
 * @param {Object} params 固定筛选条件
 * @param {number} maxRows 安全上限，默认 20000
 */
export async function fetchAllPages(fetcher, params, maxRows = 20000) {
  const pageSize = 500
  const first = await fetcher({ ...params, pageNum: 1, pageSize })
  const rows = (first.rows || []).slice()
  const total = Number(first.total || rows.length)
  let page = 1
  while (rows.length < total && rows.length < maxRows) {
    page++
    const next = await fetcher({ ...params, pageNum: page, pageSize })
    const batch = next.rows || []
    if (!batch.length) break
    rows.push(...batch)
  }
  return rows.slice(0, maxRows)
}
