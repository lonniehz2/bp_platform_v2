# -*- coding: utf-8 -*-
"""按 console.html 的真实路径修正 SPA 的 API 封装"""
import io
import os

P = r'D:\Work\业务平台开发\frontend\src\api\modules.js'
s = io.open(P, encoding='utf-8').read()

FIX = [
    # 催缴：真实是 dunnings
    ("  arrears: (params) => req.get('/fin/arrears', { params }),",
     "  // console 使用 /fin/dunnings（催缴），不是 /fin/arrears\n"
     "  arrears: (params) => req.get('/fin/dunnings', { params }),\n"
     "  dunningByBill: (billId) => req.get('/fin/dunnings/by-bill',\n"
     "    { params: { billId } }),\n"
     "  dunningScan: () => req.post('/fin/dunnings/scan'),"),
    # 流水：真实是 cash-flows
    ("  cashflow: (params) => req.get('/fin/cashflow', { params }),",
     "  // console 使用 /fin/cash-flows\n"
     "  cashflow: (params) => req.get('/fin/cash-flows', { params }),\n"
     "  cashflowNet: (params) => req.get('/fin/cash-flows/net', { params }),\n"
     "  reconciles: (params) => req.get('/fin/reconciles', { params }),"),
    # 押金按合同查
    ("  deposits: (params) => req.get('/fin/deposits', { params }),",
     "  deposits: (params) => req.get('/fin/deposits', { params }),\n"
     "  depositByContract: (contractId) =>\n"
     "    req.get('/fin/deposits/by-contract', { params: { contractId } }),"),
    # 空间树（console 有）
    ("  children: (parentId) => req.get('/spaces/children', { params: { parentId } })",
     "  children: (parentId) => req.get('/spaces/children', { params: { parentId } }),\n"
     "  tree: (params) => req.get('/spaces/tree', { params })"),
    # 公示完成校验
    ("  close: (id, remark) => req.post(`/publicities/${id}/close`, { remark }),",
     "  allocationCheck: (orgId) => req.get('/publicities/allocation-check',\n"
     "    { params: { orgId } }),\n"
     "  close: (id, remark) => req.post(`/publicities/${id}/close`, { remark }),"),
    # 人员按证件号
    ("  get: (id) => req.get(`/persons/${id}`)",
     "  get: (id) => req.get(`/persons/${id}`),\n"
     "  byIdCard: (idCard) => req.get('/persons/by-id-card', { params: { idCard } })"),
    # 合同到期批量
    ("  cohabitants: (contractId) => req.get(`/contracts/${contractId}/cohabitants`)",
     "  cohabitants: (contractId) => req.get(`/contracts/${contractId}/cohabitants`),\n"
     "  expireDue: () => req.post('/contracts/expire-due')"),
    # 信用：按人查 + 扫描过期
    ("  checkBan: (personId) => req.get('/credits/check-ban', { params: { personId } })",
     "  checkBan: (personId) => req.get('/credits/check-ban', { params: { personId } }),\n"
     "  scanExpired: () => req.post('/credits/scan-expired')"),
    # 告警统计
    ("  toWorkOrder: (id, data) => req.post(`/alerts/${id}/to-workorder`, data)",
     "  toWorkOrder: (id, data) => req.post(`/alerts/${id}/to-workorder`, data),\n"
     "  stats: () => req.get('/alerts/stats')"),
]

n = 0
for old, new in FIX:
    if old in s:
        s = s.replace(old, new, 1)
        n += 1
    else:
        print('  !! 锚点缺失：%s' % old[:52])

# 年审模块（SPA 完全缺失）
if 'annualReviewApi' not in s:
    s = s.rstrip() + '''

/** 年审复核（console 有、SPA 原先完全缺失） */
export const annualReviewApi = {
  page: (params) => req.get('/annual-reviews', { params }),
  get: (id) => req.get(`/annual-reviews/${id}`),
  create: (data) => req.post('/annual-reviews', data),
  batch: (data) => req.post('/annual-reviews/batch', data),
  review: (id, data) => req.post(`/annual-reviews/${id}/review`, data)
}
'''
    print('  + 新增 annualReviewApi')

io.open(P, 'w', encoding='utf-8').write(s)
print('\n已修正 %d/%d 处' % (n, len(FIX)))
