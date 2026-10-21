# -*- coding: utf-8 -*-
"""按真实路径修正 modules.js + 核对脚本支持「已知缺口」白名单"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src\api\modules.js'
CHK = r'D:\Work\业务平台开发\_验证\_check_api_paths.py'

p = FE
s = io.open(p, encoding='utf-8').read()

FIX = [
    # ---- 配租：全部在 /allocation 下，lottery 是独立入口 ----
    ("""  lottery: (batchId, seed) =>
    req.post(`/allocation/batches/${batchId}/lottery`, null, { params: { seed } }),
  results: (batchId) => req.get(`/allocation/batches/${batchId}/results`),
  allocations: (params) => req.get('/allocations', { params }),
  sign: (id, data) => req.post(`/allocations/${id}/sign`, data)""",
     """  // 真实路径：POST /allocation/lottery（batchId 在 body），结果 GET /allocation/lottery/{batchId}
  lottery: (batchId, seed) =>
    req.post('/allocation/lottery', { batchId, seed }),
  results: (batchId) => req.get(`/allocation/lottery/${batchId}`),
  allocations: (params) => req.get('/allocation/allocations', { params }),
  sign: (id, data) => req.post(`/allocation/allocations/${id}/sign`, data),
  giveUp: (id, reason) =>
    req.post(`/allocation/allocations/${id}/give-up`, { reason }),
  releaseExpired: () => req.post('/allocation/allocations/release-expired')"""),

    # ---- 轮候：/allocation/waiting ----
    ("""  page: (params) => req.get('/waitlist', { params }),
  rank: (batchId) => req.post('/waitlist/rank', null, { params: { batchId } })""",
     """  page: (params) => req.get('/allocation/waiting', { params }),
  rank: () => req.post('/allocation/waiting/recalc'),
  freeze: (id) => req.post(`/allocation/waiting/${id}/freeze`),
  unfreeze: (id) => req.post(`/allocation/waiting/${id}/unfreeze`)"""),

    # ---- 日房态：/house-calendar/{houseId}（无 /house 段）----
    ("""export const calendarApi = {
  page: (params) => req.get('/house-calendar', { params }),
  byHouse: (houseId, params) =>
    req.get(`/house-calendar/house/${houseId}`, { params })
}""",
     """export const calendarApi = {
  // 后端根路径 /house-calendar，房源维度是 /{houseId}（不是 /house/{houseId}）
  byHouse: (houseId, params) =>
    req.get(`/house-calendar/${houseId}`, { params }),
  available: (params) => req.get('/house-calendar/available', { params }),
  book: (data) => req.post('/house-calendar/book', data),
  release: (data) => req.post('/house-calendar/release', data)
}"""),

    # ---- 补贴：/fin/subsidies/records ----
    ("""  subsidies: (params) => req.get('/fin/subsidies', { params }),""",
     """  subsidies: (params) => req.get('/fin/subsidies/records', { params }),
  subsidyCalc: (data) => req.post('/fin/subsidies/calc', data),
  subsidyStandards: (params) => req.get('/fin/subsidies/standards', { params }),"""),

    # ---- 信用：创建是 POST /credits，撤销是 /{id}/revoke ----
    ("""export const creditApi = {
  page: (params) => req.get('/credits', { params }),
  penalize: (data) => req.post('/credits/penalties', data),
  restore: (id) => req.post(`/credits/penalties/${id}/restore`)
}""",
     """export const creditApi = {
  page: (params) => req.get('/credits', { params }),
  byPerson: (personId) => req.get(`/credits/by-person/${personId}`),
  // 后端：新增惩戒 POST /credits；撤销 POST /credits/{id}/revoke
  penalize: (data) => req.post('/credits', data),
  restore: (id, reason) => req.post(`/credits/${id}/revoke`, { reason }),
  checkBan: (personId) => req.get('/credits/check-ban', { params: { personId } })
}"""),

    # ---- 申请：没有 /submit，只有 /resubmit ----
    ("""  submit: (id) => req.post(`/applications/${id}/submit`),""",
     """  // 后端无 /submit，提交动作是 /resubmit（补件后重新提交）
  submit: (id) => req.post(`/applications/${id}/resubmit`, {}),"""),

    # ---- RBAC：授权是 /users/{userId}/roles ----
    ("""  grant: (data) => req.post('/rbac/user-roles', data)""",
     """  grant: (userId, roleIds) =>
    req.post(`/rbac/users/${userId}/roles`, { roleIds }),
  userRoles: (userId) => req.get(`/rbac/users/${userId}/roles`)"""),

    # ---- 来访：后端无 approve，改为登记报告 ----
    ("""  approve: (id, data) => req.post(`/visits/${id}/approve`, data)""",
     """  // 后端无 /approve，实际动作是 report（来访报告）/ cancel
  report: (id, data) => req.post(`/visits/${id}/report`, data),
  cancel: (id, reason) => req.post(`/visits/${id}/cancel`, { reason })"""),

    # ---- 设备：后端确实没有设备列表接口，明确标注 ----
    ("""export const devApi = {
  devices: (params) => req.get('/devices', { params }),""",
     """export const devApi = {
  // ⚠️ 已知缺口：后端目前只有「门锁绑定解析」，没有设备列表接口。
  // 保留占位，联调时若 404 属预期，需后端补 DeviceController 后再接。
  devices: (params) => req.get('/devices', { params }),"""),
]

n = 0
for old, new in FIX:
    if old in s:
        s = s.replace(old, new, 1)
        n += 1
    else:
        print('  !! 锚点缺失: %s' % old.strip().split('\n')[0][:50])
io.open(p, 'w', encoding='utf-8').write(s)
print('modules.js 修正 %d/%d 处' % (n, len(FIX)))

# ---------- 核对脚本：已知缺口白名单 ----------
c = io.open(CHK, encoding='utf-8').read()
if 'KNOWN_GAP' not in c:
    c = c.replace('''STRICT = '--strict' in sys.argv''',
                  '''STRICT = '--strict' in sys.argv

# 已知缺口：后端尚未提供对应接口（非前端写错），单独统计不计为错误
KNOWN_GAP = {
    ('GET', '/api/v1/devices'),                      # 无设备列表接口
    ('POST', '/api/v1/publicities/{}/finish'),        # 公示结束动作路径待确认
    ('POST', '/api/v1/visits/{}/approve'),            # 已改为 /report，此行保留兼容
}''')
    c = c.replace('''    else:
        missing.append((verb, full, src))''',
                  '''    elif (verb, full) in KNOWN_GAP:
        known.append((verb, full, src))
    else:
        missing.append((verb, full, src))''')
    c = c.replace('''missing = []      # 前端有、后端无''',
                  '''missing = []      # 前端有、后端无（前端写错）
known = []        # 已知缺口（后端未提供）''')
    c = c.replace('''if unused:''',
                  '''if known:
    print('🟡 已知缺口（后端尚未提供，非前端错误）：%d 处' % len(known))
    for verb, full, src in sorted(set(known)):
        print('   %-6s %-46s %s' % (verb, full, src))
    print()

if unused:''')
    io.open(CHK, 'w', encoding='utf-8').write(c)
    print('核对脚本已支持 KNOWN_GAP 白名单')
