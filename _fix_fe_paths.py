# -*- coding: utf-8 -*-
"""修正前端接口路径（6 处）+ 新增字典能力 + 字典下拉接入"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}
PATCH = []

# ==================== 1) 重写 modules.js（修正路径 + 补字典/工单） ====================
F['src/api/modules.js'] = '''import req from './request'

/**
 * 接口封装。
 *
 * ⚠️ 路径规范（已按后端 @RequestMapping 逐个核对，不再凭习惯命名）：
 *   资金类统一在 /fin 下：/fin/bills、/fin/payments、/fin/deposits、/fin/subsidies
 *   工单在 /workorders（无横线）
 *   核销是 /fin/payments/{paymentId}/allocate（paymentId 在路径上，不是 body）
 *   组织子节点是 /orgs/children（不是 /orgs/tree）
 *   审核轨迹是 /applications/{id}/reviews（不是 /records）
 */

/** 认证 */
export const authApi = {
  login: (data) => req.post('/auth/login', data),
  logout: () => req.post('/auth/logout'),
  me: () => req.get('/auth/me')
}

/** 系统支撑：字典 / 参数 / 审计（下拉选项与政策参数都从这里取） */
export const sysApi = {
  dicts: (dictType) => req.get(`/sys/dicts/${dictType}`),
  dictMap: (dictType) => req.get(`/sys/dicts/${dictType}/map`),
  dictTypes: () => req.get('/sys/dicts'),
  configs: (group) => req.get('/sys/configs', { params: { group } }),
  auditLogs: (params) => req.get('/sys/audit-logs', { params })
}

/** 组织与空间 */
export const orgApi = {
  page: (params) => req.get('/orgs', { params }),
  children: (parentId) => req.get('/orgs/children', { params: { parentId } }),
  get: (id) => req.get(`/orgs/${id}`)
}

export const houseApi = {
  page: (params) => req.get('/houses', { params }),
  get: (id) => req.get(`/houses/${id}`),
  setStatus: (id, data) => req.post(`/houses/${id}/status`, data)
}

/** 申请与审核 */
export const applicationApi = {
  page: (params) => req.get('/applications', { params }),
  get: (id) => req.get(`/applications/${id}`),
  create: (data) => req.post('/applications', data),
  submit: (id) => req.post(`/applications/${id}/submit`),
  accept: (id) => req.post(`/applications/${id}/accept`),
  review: (id, data) => req.post(`/applications/${id}/review`, data),
  resubmit: (id, data) => req.post(`/applications/${id}/resubmit`, data),
  cancel: (id) => req.post(`/applications/${id}/cancel`),
  reviews: (id) => req.get(`/applications/${id}/reviews`)
}

/** 公示 */
export const publicityApi = {
  page: (params) => req.get('/publicities', { params }),
  create: (data) => req.post('/publicities', data),
  finish: (id) => req.post(`/publicities/${id}/finish`)
}

/** 轮候 */
export const waitlistApi = {
  page: (params) => req.get('/waitlist', { params }),
  rank: (batchId) => req.post('/waitlist/rank', null, { params: { batchId } })
}

/** 配租批次与摇号 */
export const allocationApi = {
  batches: (params) => req.get('/allocation/batches', { params }),
  createBatch: (data) => req.post('/allocation/batches', data),
  addHouses: (batchId, houseIds) =>
    req.post(`/allocation/batches/${batchId}/houses`, houseIds),
  lottery: (batchId, seed) =>
    req.post(`/allocation/batches/${batchId}/lottery`, null, { params: { seed } }),
  results: (batchId) => req.get(`/allocation/batches/${batchId}/results`),
  allocations: (params) => req.get('/allocations', { params }),
  sign: (id, data) => req.post(`/allocations/${id}/sign`, data)
}

/** 合同 */
export const contractApi = {
  page: (params) => req.get('/contracts', { params }),
  get: (id) => req.get(`/contracts/${id}`),
  cohabitants: (contractId) => req.get(`/contracts/${contractId}/cohabitants`)
}

/** 账务（全部在 /fin 下面） */
export const financeApi = {
  bills: (params) => req.get('/fin/bills', { params }),
  bill: (id) => req.get(`/fin/bills/${id}`),
  generate: (data) => req.post('/fin/bills/generate', data),
  generateBatch: (data) => req.post('/fin/bills/generate-batch', data),
  scanOverdue: () => req.post('/fin/bills/scan-overdue'),
  waive: (id, data) => req.post(`/fin/bills/${id}/waive`, data),
  payments: (params) => req.get('/fin/payments', { params }),
  /** 核销：paymentId 在路径上 */
  allocate: (paymentId, billId, amount) =>
    req.post(`/fin/payments/${paymentId}/allocate`, { billId, amount }),
  deposits: (params) => req.get('/fin/deposits', { params }),
  subsidies: (params) => req.get('/fin/subsidies', { params }),
  feeItems: (params) => req.get('/fin/fee-items', { params })
}

/** 工单与维保（/workorders，无横线） */
export const workOrderApi = {
  page: (params) => req.get('/workorders', { params }),
  get: (id) => req.get(`/workorders/${id}`),
  create: (data) => req.post('/workorders', data),
  assign: (id, data) => req.post(`/workorders/${id}/assign`, data),
  accept: (id) => req.post(`/workorders/${id}/accept`),
  start: (id) => req.post(`/workorders/${id}/start`),
  finish: (id, data) => req.post(`/workorders/${id}/finish`, data),
  logs: (id) => req.get(`/workorders/${id}/logs`)
}

/** 告警与规则引擎 */
export const alertApi = {
  page: (params) => req.get('/alerts', { params }),
  toWorkOrder: (id, data) => req.post(`/alerts/${id}/to-workorder`, data)
}

export const ruleApi = {
  rulesets: (params) => req.get('/rules/rulesets', { params }),
  activeRuleset: (params) => req.get('/rules/rulesets/active', { params }),
  rules: (rulesetId) => req.get(`/rules/rulesets/${rulesetId}/rules`),
  addRule: (rulesetId, data) => req.post(`/rules/rulesets/${rulesetId}/rules`, data),
  execute: (rulesetId, data) => req.post(`/rules/rulesets/${rulesetId}/execute`, data),
  publish: (id) => req.post(`/rules/rulesets/${id}/publish`),
  logs: (params) => req.get('/rules/logs', { params }),
  stats: (rulesetId) => req.get('/rules/stats', { params: { rulesetId } })
}

/** 报表与大屏 */
export const rptApi = {
  reports: (params) => req.get('/rpt/reports', { params }),
  query: (data) => req.post('/rpt/reports/query', data),
  export: (data) => req.post('/rpt/exports', data),
  taskContent: (id) => req.get(`/rpt/exports/${id}/content`),
  screens: (params) => req.get('/rpt/screens', { params }),
  screenData: (code, orgId) =>
    req.get(`/rpt/screens/${code}/data`, { params: { orgId } }),
  metrics: (orgId) => req.get('/rpt/metrics/current', { params: { orgId } }),
  snapshot: (orgId) => req.post('/rpt/metrics/snapshot', null, { params: { orgId } })
}

/** 设备与通行记录 */
export const devApi = {
  devices: (params) => req.get('/devices', { params }),
  accessRecords: (params) => req.get('/access-records', { params }),
  traceByHouse: (houseId, params) =>
    req.get(`/access-records/trace/house/${houseId}`, { params }),
  traceByPerson: (personId, params) =>
    req.get(`/access-records/trace/person/${personId}`, { params }),
  idle: (params) => req.get('/access-records/idle', { params }),
  untrustedRatio: (params) => req.get('/access-records/untrusted-ratio', { params })
}

/** 消息与待办 */
export const msgApi = {
  todos: (params) => req.get('/messages/todos', { params }),
  unread: (userId) => req.get('/messages/todos/unread', { params: { userId } }),
  read: (id) => req.post(`/messages/todos/${id}/read`),
  done: (id) => req.post(`/messages/todos/${id}/done`),
  createTodo: (data) => req.post('/messages/todos', data),
  send: (data) => req.post('/messages/send', data),
  records: (params) => req.get('/messages/records', { params }),
  templates: (params) => req.get('/messages/templates', { params })
}

/** 钥匙包与授权对账（★ 级） */
export const keyringApi = {
  byPerson: (personId) => req.get(`/keyring/person/${personId}`),
  summary: (personId) => req.get(`/keyring/person/${personId}/summary`),
  add: (data) => req.post('/keyring', data),
  setStatus: (id, status) => req.post(`/keyring/${id}/status`, { status }),
  remove: (id) => req.post(`/keyring/${id}/remove`)
}

export const grantApi = {
  page: (params) => req.get('/grants', { params }),
  reconcileRun: (lockId) =>
    req.post('/grant-reconcile/run', null, { params: { lockId } }),
  diffs: (params) => req.get('/grant-reconcile/diffs', { params }),
  handleDiff: (id, data) => req.post(`/grant-reconcile/diffs/${id}/handle`, data),
  reconcileStats: () => req.get('/grant-reconcile/stats'),
  auditLogs: (params) => req.get('/grant-audit-logs', { params })
}
'''

# ==================== 2) 字典封装 ====================
F['src/composables/useDict.js'] = '''import { ref, onMounted } from 'vue'
import { sysApi } from '@/api/modules'

/**
 * 字典下拉（替代硬编码枚举）。
 *
 * 用法：
 *   const { options, label } = useDict('HOUSE_TYPE')
 *   <el-option v-for="o in options" :key="o.value" :label="o.label" :value="o.value" />
 *
 * 设计：
 * - 同类型并发只请求一次（模块级缓存）
 * - 后端不可用时**不抛错**，退化为空数组（页面仍可用，只是下拉为空）
 * - 支持 fallback：由调用方传入静态兜底项，保证字典服务异常时业务不中断
 */
const cache = new Map()      // dictType -> options[]
const pending = new Map()    // dictType -> Promise

export function useDict(dictType, fallback = []) {
  const options = ref(cache.get(dictType) || fallback)

  async function load() {
    if (cache.has(dictType)) {
      options.value = cache.get(dictType)
      return
    }
    try {
      let p = pending.get(dictType)
      if (!p) {
        p = sysApi.dicts(dictType)
        pending.set(dictType, p)
      }
      const list = await p
      const opts = (list || []).map((d) => ({
        value: d.dictCode,
        label: d.dictLabel,
        raw: d
      }))
      cache.set(dictType, opts)
      options.value = opts.length ? opts : fallback
    } catch (e) {
      // 字典不可用不应阻断页面
      options.value = fallback
    } finally {
      pending.delete(dictType)
    }
  }

  /** 编码 → 中文标签 */
  function label(code) {
    const hit = (options.value || []).find((o) => o.value === code)
    return hit ? hit.label : code
  }

  onMounted(load)

  return { options, label, reload: load }
}

/** 清除缓存（字典维护后调用） */
export function clearDictCache() {
  cache.clear()
}
'''

# ==================== 3) 打补丁：页面与 H5 路径、字典接入、大屏需登录 ====================
PATCH = [
    # --- Houses.vue：房源类型改用字典 ---
    ('src/views/Houses.vue',
     [('''      <el-select v-model="query.houseType" placeholder="房源类型" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="t in types" :key="t" :label="t" :value="t" />
      </el-select>''',
       '''      <el-select v-model="query.houseType" placeholder="房源类型" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="t in houseTypeOptions" :key="t.value"
                   :label="t.label" :value="t.value" />
      </el-select>'''),
      ('''import { houseApi } from '@/api/modules\'''',
       '''import { houseApi } from '@/api/modules'
import { useDict } from '@/composables/useDict\''''),
      ('''const statuses = ['VACANT', 'PENDING_ALLOC', 'ALLOCATED', 'OCCUPIED',
  'MAINTENANCE', 'PENDING_EXIT', 'LOCKED']
const types = ['PUBLIC_RENTAL', 'APARTMENT', 'DORMITORY', 'HOTEL']''',
       '''// 房源状态来自后端枚举（无独立字典项），类型走系统字典 HOUSE_TYPE
const statuses = ['VACANT', 'PENDING_ALLOC', 'ALLOCATED', 'OCCUPIED',
  'MAINTENANCE', 'PENDING_EXIT', 'LOCKED']
const { options: houseTypeOptions } = useDict('HOUSE_TYPE', [
  { value: 'PUBLIC_RENTAL', label: '公租房' },
  { value: 'APARTMENT', label: '公寓' },
  { value: 'DORMITORY', label: '宿舍' },
  { value: 'HOTEL', label: '酒店/民宿' }
])''')]),

    # --- Applications.vue：保障类型改字典 + 审核轨迹路径 ---
    ('src/views/Applications.vue',
     [('''        <el-form-item label="保障类型">
          <el-select v-model="form.securityType">
            <el-option label="公租房" value="PUBLIC" />
            <el-option label="保障性租赁住房" value="AFFORDABLE" />
            <el-option label="人才公寓" value="TALENT" />
            <el-option label="廉租住房" value="LOW_RENT" />
          </el-select>
        </el-form-item>''',
       '''        <el-form-item label="保障类型">
          <el-select v-model="form.securityType">
            <el-option v-for="o in securityTypeOptions" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>'''),
      ('''import { applicationApi } from '@/api/modules\'''',
       '''import { applicationApi } from '@/api/modules'
import { useDict } from '@/composables/useDict\''''),
      ('''const statuses = ['DRAFT', 'SUBMITTED', 'ACCEPTED', 'REVIEWING', 'SUPPLEMENT',
  'APPROVED', 'REJECTED', 'CANCELLED']''',
       '''const statuses = ['DRAFT', 'SUBMITTED', 'ACCEPTED', 'REVIEWING', 'SUPPLEMENT',
  'APPROVED', 'REJECTED', 'CANCELLED']

// 保障类型走系统字典（可后台维护，无需改前端）
const { options: securityTypeOptions } = useDict('SECURITY_TYPE', [
  { value: 'PUBLIC', label: '公租房' },
  { value: 'AFFORDABLE', label: '保障性租赁住房' },
  { value: 'TALENT', label: '人才公寓' },
  { value: 'LOW_RENT', label: '廉租住房' }
])'''),
      ('records.value = await applicationApi.records(row.id)',
       '// 后端真实路径是 /reviews（审核记录）\\n  records.value = await applicationApi.reviews(row.id)')]),

    # --- Orgs.vue：组织子节点路径 ---
    ('src/views/Orgs.vue',
     [('''    const data = await orgApi.tree()
    tree.value = Array.isArray(data) ? data : (data?.rows || [])''',
       '''    // 后端只有 /orgs/children（按 parentId 取子节点），无整棵树接口：
    // 这里从根节点（parentId 空）开始逐层展开，最多 3 层，避免一次拉全表
    const roots = await orgApi.children()
    const level1 = Array.isArray(roots) ? roots : (roots?.rows || [])
    for (const n of level1) {
      try {
        const ch = await orgApi.children(n.id)
        const list = Array.isArray(ch) ? ch : (ch?.rows || [])
        if (list.length) n.children = list
      } catch (e) { /* 忽略单节点失败 */ }
    }
    tree.value = level1''')]),

    # --- Bills.vue：核销签名变化 ---
    ('src/views/Bills.vue',
     [('''    await financeApi.allocate(allocateForm.paymentId, currentBill.value.id,
      allocateForm.amount)''',
       '''    // 正确签名：allocate(paymentId, billId, amount)
    await financeApi.allocate(allocateForm.paymentId, currentBill.value.id,
      allocateForm.amount)''')]),

    # --- H5 报修：/workorders ---
    ('src/h5/views/H5Repairs.vue',
     [('''import req from '@/api/request\'''',
       '''import { workOrderApi } from '@/api/modules\''''),
      ('''    await req.post('/work-orders', {
      orderType: 'REPAIR',
      source: 'TENANT_APP',
      title: `住户报修：${form.type}`,
      description: form.description,
      priority: form.urgency,
      personId: localStorage.getItem('bp_person_id') || undefined
    })''',
       '''    // 后端真实路径：POST /api/v1/workorders
    await workOrderApi.create({
      orderType: 'REPAIR',
      source: 'TENANT_APP',
      title: `住户报修：${form.type}`,
      description: form.description,
      priority: form.urgency,
      personId: localStorage.getItem('bp_person_id') || undefined
    })''')]),

    # --- Messages.vue：用封装好的 msgApi ---
    ('src/views/Messages.vue',
     [('await req.post(`/messages/todos/${row.id}/read`)', 'await msgApi.read(row.id)'),
      ('await req.post(`/messages/todos/${row.id}/done`)', 'await msgApi.done(row.id)'),
      ("await req.post('/messages/todos', { ...form, todoType: 'REMIND' })",
       "await msgApi.createTodo({ ...form, todoType: 'REMIND' })"),
      ('''import req from '@/api/request'
''', '')]),

    # --- 大屏路由：必须登录（原先 public 是安全隐患） ---
    ('src/router/index.js',
     [('''    component: () => import('@/screen/ScreenApp.vue'),
    meta: { public: true }''',
       '''    component: () => import('@/screen/ScreenApp.vue'),
    // 大屏展示业务数据，必须登录（原 meta.public 属安全隐患，已移除）
    meta: {}''')]),
]

for rel, pairs in PATCH:
    p = os.path.join(BASE, rel.replace('/', '\\'))
    s = io.open(p, encoding='utf-8').read()
    n = 0
    for old, new in pairs:
        if old in s:
            s = s.replace(old, new, 1)
            n += 1
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  %-26s 修改 %d/%d 处' % (rel, n, len(pairs)))

for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    print('  + %-26s 重写' % rel)
