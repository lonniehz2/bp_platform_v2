# -*- coding: utf-8 -*-
"""导出：分页拉全量（后端 pageSize 上限 500）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'frontend', 'src')

# csv.js 增加分页拉取
p = os.path.join(SRC, 'utils', 'csv.js')
s = io.open(p, encoding='utf-8').read()
if 'fetchAllPages' not in s:
    s += '''

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
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('csv.js 已加 fetchAllPages')

# Contracts
p = os.path.join(SRC, 'views', 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
s = s.replace("import { downloadCsv } from '@/utils/csv'",
              "import { downloadCsv, fetchAllPages } from '@/utils/csv'", 1)
s = s.replace('''    const d = await contractApi.page({
      pageNum: 1, pageSize: 5000,
      orgId: q.orgId || undefined,
      contractStatus: q.contractStatus || undefined,
      keyword: q.keyword || undefined
    })
    const rows = d.rows || []''',
              '''    const rows = await fetchAllPages((params) => contractApi.page(params), {
      orgId: q.orgId || undefined,
      contractStatus: q.contractStatus || undefined,
      keyword: q.keyword || undefined
    })''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('合同导出改为分页全量')

# Bills
p = os.path.join(SRC, 'views', 'Bills.vue')
s = io.open(p, encoding='utf-8').read()
s = s.replace("import { downloadCsv } from '@/utils/csv'",
              "import { downloadCsv, fetchAllPages } from '@/utils/csv'", 1)
s = s.replace('''    const d = await financeApi.bills({
      pageNum: 1, pageSize: 5000,
      orgId: q.orgId || undefined,
      status: q.billStatus || undefined,
      billPeriod: q.billPeriod || undefined,
      houseId: q.houseId || undefined
    })
    const rows = d.rows || []''',
              '''    const rows = await fetchAllPages((params) => financeApi.bills(params), {
      orgId: q.orgId || undefined,
      status: q.billStatus || undefined,
      billPeriod: q.billPeriod || undefined,
      houseId: q.houseId || undefined
    })''', 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('账单导出改为分页全量')
