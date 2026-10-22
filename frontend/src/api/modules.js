import { DICT_TYPE_LABEL } from '@/constants/enums'
import req from './request'

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
  // 后端无「列出全部字典类型」接口（/sys/dicts 需要 dictType），
  // 由前端常量提供，避免 400
  dictTypes: () => Promise.resolve(Object.keys(DICT_TYPE_LABEL)),
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
  setStatus: (id, data) => req.post(`/houses/${id}/status`, data),
  create: (data) => req.post('/houses', data)
}

/** 申请与审核 */
export const applicationApi = {
  page: (params) => req.get('/applications', { params }),
  get: (id) => req.get(`/applications/${id}`),
  create: (data) => req.post('/applications', data),
  // 后端无 /submit，提交动作是 /resubmit（补件后重新提交）
  submit: (id) => req.post(`/applications/${id}/resubmit`, {}),
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
  // 公示状态流转由既有 PublicityReviewController 提供；后端无 finish，用 close
  allocationCheck: (orgId) => req.get('/publicities/allocation-check',
    { params: { orgId } }),
  close: (id, remark) => req.post(`/publicities/${id}/close`, { remark }),
  finish: (id, remark) => req.post(`/publicities/${id}/close`, { remark })
}

/** 轮候 */
export const waitlistApi = {
  page: (params) => req.get('/allocation/waiting', { params }),
  rank: () => req.post('/allocation/waiting/recalc'),
  freeze: (id) => req.post(`/allocation/waiting/${id}/freeze`),
  unfreeze: (id) => req.post(`/allocation/waiting/${id}/unfreeze`)
}

/** 配租批次与摇号 */
export const allocationApi = {
  batches: (params) => req.get('/allocation/batches', { params }),
  createBatch: (data) => req.post('/allocation/batches', data),
  addHouses: (batchId, houseIds) =>
    req.post(`/allocation/batches/${batchId}/houses`, houseIds),
  // 真实路径：POST /allocation/lottery（batchId 在 body），结果 GET /allocation/lottery/{batchId}
  lottery: (batchId, seed) =>
    req.post('/allocation/lottery', { batchId, seed }),
  results: (batchId) => req.get(`/allocation/lottery/${batchId}`),
  allocations: (params) => req.get('/allocation/allocations', { params }),
  sign: (id, data) => req.post(`/allocation/allocations/${id}/sign`, data),
  setBatchStatus: (id, batchStatus) =>
    req.post(`/allocation/batches/${id}/status`, { batchStatus }),
  giveUp: (id, reason) =>
    req.post(`/allocation/allocations/${id}/give-up`, { reason }),
  releaseExpired: () => req.post('/allocation/allocations/release-expired'),
  waiting: (params) => req.get('/allocation/waiting', { params }),
  recalcWaiting: () => req.post('/allocation/waiting/recalc'),
  giveUp: (id, reason) =>
    req.post(`/allocation/allocations/${id}/give-up`, { reason }),
  releaseExpired: () => req.post('/allocation/allocations/release-expired')
}

/** 合同 */
export const contractApi = {
  page: (params) => req.get('/contracts', { params }),
  get: (id) => req.get(`/contracts/${id}`),
  cohabitants: (contractId) => req.get(`/contracts/${contractId}/cohabitants`),
  expireDue: () => req.post('/contracts/expire-due'),
  create: (data) => req.post('/contracts', data),
  // 状态推进：草稿 → 待签约 → 签约中 → 履约中
  submitSign: (id) => req.post(`/contracts/${id}/submit-sign`),
  startSigning: (id, data) => req.post(`/contracts/${id}/start-signing`, data || {}),
  // 签名接口：SignCmd{signVendor, signFileUrl, signFlowId, reason}
  sign: (id, data) => req.post(`/contracts/${id}/sign`, data),
  // 续签：RenewCmd{newLeaseEnd, newMonthlyRent}
  renew: (id, data) => req.post(`/contracts/${id}/renew`, data),
  terminate: (id, data) => req.post(`/contracts/${id}/terminate`, data),
  cancel: (id, reason) => req.post(`/contracts/${id}/cancel`, { reason })
}

/** 账务（全部在 /fin 下面） */
export const financeApi = {
  bills: (params) => req.get('/fin/bills', { params }),
  orgs: (params) => req.get('/orgs', { params }),
  feeItems: (params) => req.get('/fin/fee-items', { params }),
  bill: (id) => req.get(`/fin/bills/${id}`),
  generate: (data) => req.post('/fin/bills/generate', data),
  generateBatch: (data) => req.post('/fin/bills/generate-batch', data),
  generateShared: (data) => req.post('/fin/bills/generate-shared', data),
  scanOverdue: () => req.post('/fin/bills/scan-overdue'),
  waive: (id, data) => req.post(`/fin/bills/${id}/waive`, data),
  payments: (params) => req.get('/fin/payments', { params }),
  createPayment: (data) => req.post('/fin/payments', data),
  cancelBill: (id, reason) => req.post(`/fin/bills/${id}/cancel`, { reason }),
  billGenerateBatch: (data) => req.post('/fin/bills/generate-batch', data),
  /** 核销：paymentId 在路径上 */
  allocate: (paymentId, billId, amount) =>
    req.post(`/fin/payments/${paymentId}/allocate`, { billId, amount }),
  deposits: (params) => req.get('/fin/deposits', { params }),
  depositByContract: (contractId) =>
    req.get('/fin/deposits/by-contract', { params: { contractId } }),
  subsidies: (params) => req.get('/fin/subsidies/records', { params }),
  subsidyCalc: (data) => req.post('/fin/subsidies/calc', data),
  subsidyStandards: (params) => req.get('/fin/subsidies/standards', { params }),
  feeItems: (params) => req.get('/fin/fee-items', { params }),
  // console 使用 /fin/dunnings（催缴），不是 /fin/arrears
  arrears: (params) => req.get('/fin/dunnings', { params }),
  dunningByBill: (billId) => req.get('/fin/dunnings/by-bill',
    { params: { billId } }),
  // 后端 scan 是 GET（不是 POST）
  dunningScan: (params) => req.get('/fin/dunnings/scan', { params }),
  // console 使用 /fin/cash-flows
  cashflow: (params) => req.get('/fin/cash-flows', { params }),
  cashflowNet: (params) => req.get('/fin/cash-flows/net', { params }),
  reconciles: (params) => req.get('/fin/reconciles', { params }),
  refunds: (params) => req.get('/fin/refunds', { params })
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
  toWorkOrder: (id, data) => req.post(`/alerts/${id}/to-workorder`, data),
  stats: () => req.get('/alerts/stats')
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
  // 下载导出文件：必须以 blob 接收，否则拦截器会把二进制当 JSON 解析
  downloadTask: (id) => req.get(`/rpt/exports/${id}/download`, { responseType: 'blob' }),
  screens: (params) => req.get('/rpt/screens', { params }),
  screenData: (code, orgId) =>
    req.get(`/rpt/screens/${code}/data`, { params: { orgId } }),
  metrics: (orgId) => req.get('/rpt/metrics/current', { params: { orgId } }),
  snapshot: (orgId) => req.post('/rpt/metrics/snapshot', null, { params: { orgId } })
}

/** 设备与通行记录 */
export const devApi = {
  // 设备列表接口已由 DeviceController 补齐（GET /api/v1/devices）
  devices: (params) => req.get('/devices', { params }),
  deviceStats: () => req.get('/devices/stats'),
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
  // 统一待办中心：跨模块待办计数（申请/合同/退租/换房/年审/工单/消息）
  todoOverview: () => req.get('/todos/overview'),
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

/** 人员 / 空间（补齐剩余模块） */
export const personApi = {
  page: (params) => req.get('/persons', { params }),
  get: (id) => req.get(`/persons/${id}`),
  byIdCard: (idCard) => req.get('/persons/by-id-card', { params: { idCard } })
}

export const spaceApi = {
  page: (params) => req.get('/spaces', { params }),
  get: (id) => req.get(`/spaces/${id}`),
  children: (parentId) => req.get('/spaces/children', { params: { parentId } }),
  tree: (params) => req.get('/spaces/tree', { params }),
  create: (data) => req.post('/spaces', data),
  remove: (id) => req.delete(`/spaces/${id}`)
}

/** 退租 / 申诉 / 信用 / 换房 */
export const terminationApi = {
  page: (params) => req.get('/terminations', { params }),
  get: (id) => req.get(`/terminations/${id}`),
  create: (data) => req.post('/terminations', data),
  approve: (id, data) => req.post(`/terminations/${id}/approve`, data)
}

export const appealApi = {
  page: (params) => req.get('/appeals', { params }),
  get: (id) => req.get(`/appeals/${id}`),
  decide: (id, data) => req.post(`/appeals/${id}/decide`, data)
}

export const creditApi = {
  page: (params) => req.get('/credits', { params }),
  byPerson: (personId) => req.get(`/credits/by-person/${personId}`),
  // 后端：新增惩戒 POST /credits；撤销 POST /credits/{id}/revoke
  penalize: (data) => req.post('/credits', data),
  restore: (id, reason) => req.post(`/credits/${id}/revoke`, { reason }),
  checkBan: (personId) => req.get('/credits/check-ban', { params: { personId } }),
  scanExpired: () => req.post('/credits/scan-expired')
}

export const exchangeApi = {
  page: (params) => req.get('/exchanges', { params }),
  approve: (id, data) => req.post(`/exchanges/${id}/approve`, data)
}

/** 投诉 / 来访 */
export const complaintApi = {
  page: (params) => req.get('/complaints', { params }),
  handle: (id, data) => req.post(`/complaints/${id}/handle`, data)
}

export const visitApi = {
  page: (params) => req.get('/visits', { params }),
  // 后端无 /approve，实际动作是 report（来访报告）/ cancel
  report: (id, data) => req.post(`/visits/${id}/report`, data),
  cancel: (id, reason) => req.post(`/visits/${id}/cancel`, { reason })
}

/** 短租与日房态 */
export const shortRentApi = {
  page: (params) => req.get('/short-rent-orders', { params }),
  get: (id) => req.get(`/short-rent-orders/${id}`),
  cancel: (id, reason) =>
    req.post(`/short-rent-orders/${id}/cancel`, null, { params: { reason } })
}

export const calendarApi = {
  // 后端根路径 /house-calendar，房源维度是 /{houseId}（不是 /house/{houseId}）
  byHouse: (houseId, params) =>
    req.get(`/house-calendar/${houseId}`, { params }),
  ensure: (houseId, month) =>
    req.post(`/house-calendar/${houseId}/ensure?month=${month}`),
  available: (params) => req.get('/house-calendar/available', { params }),
  book: (data) => req.post('/house-calendar/book', data),
  release: (data) => req.post('/house-calendar/release', data)
}

/** 监管报送 / 开放平台 */
export const govApi = {
  tasks: (params) => req.get('/gov/reports', { params }),
  task: (id) => req.get(`/gov/reports/${id}`),
  details: (id) => req.get(`/gov/reports/${id}/details`),
  submit: (data) => req.post('/gov/reports', data),
  retry: (id) => req.post(`/gov/reports/${id}/retry`),
  stats: () => req.get('/gov/stats'),
  adapters: () => req.get('/gov/adapters')
}

export const openApi = {
  apps: (params) => req.get('/open/apps', { params }),
  createApp: (data) => req.post('/open/apps', data),
  resetSecret: (id) => req.post(`/open/apps/${id}/reset-secret`),
  apis: (params) => req.get('/open/apis', { params }),
  callLogs: (params) => req.get('/open/call-logs', { params }),
  usage: (params) => req.get('/open/usage', { params }),
  hooks: () => req.get('/open/webhooks'),
  verify: (data) => req.post('/open/verify', data)
}

/** RBAC 管理 */
export const rbacApi = {
  users: (params) => req.get('/rbac/users', { params }),
  roles: () => req.get('/rbac/roles'),
  permissions: () => req.get('/rbac/permissions'),
  grant: (userId, roleIds) =>
    req.post(`/rbac/users/${userId}/roles`, { roleIds }),
  userRoles: (userId) => req.get(`/rbac/users/${userId}/roles`)
}

/** 补贴 / 押金 / 公示 / 轮候 / 计费 / 催缴 / 流水 / 合同变更（补齐 console 已有模块） */
export const subsidyApi = {
  records: (params) => req.get('/fin/subsidies/records', { params }),
  calc: (data) => req.post('/fin/subsidies/calc', data),
  standards: (params) => req.get('/fin/subsidies/standards', { params }),
  batchGrant: (data) => req.post('/fin/subsidies/records/batch', data),
  confirm: (id) => req.post(`/fin/subsidies/records/${id}/confirm`)
}

export const contractChangeApi = {
  page: (params) => req.get('/contract-changes', { params }),
  get: (id) => req.get(`/contract-changes/${id}`),
  approve: (id, data) => req.post(`/contract-changes/${id}/approve`, data)
}

/** 年审复核（console 有、SPA 原先完全缺失） */
export const annualReviewApi = {
  page: (params) => req.get('/annual-reviews', { params }),
  get: (id) => req.get(`/annual-reviews/${id}`),
  create: (data) => req.post('/annual-reviews', data),
  batch: (data) => req.post('/annual-reviews/batch', data),
  // 后端真实动作：start 开始复核 → finish 提交结论（原 review 路径不存在）
  start: (id) => req.post(`/annual-reviews/${id}/start`),
  finish: (id, data) => req.post(`/annual-reviews/${id}/finish`, data),
  markOverdue: () => req.post('/annual-reviews/mark-overdue')
}
