const BASE = '/api/v1/platform'
const AUTH = '/api/v1/auth'
const TENANT = '350600'

function token() {
  return localStorage.getItem('platformToken') || ''
}

async function request(path, options = {}) {
  const headers = { 'X-Tenant-Id': TENANT, ...(options.headers || {}) }
  if (token()) headers.Authorization = `Bearer ${token()}`
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json; charset=utf-8'
  }
  const res = await fetch(BASE + path, { ...options, headers })
  const json = await res.json().catch(() => ({}))
  if (res.status === 401) {
    localStorage.removeItem('platformToken')
    localStorage.removeItem('platformUser')
    if (!location.hash.startsWith('#/login')) location.hash = '#/login'
  }
  if (!res.ok || json.code !== 'BP00000') {
    throw new Error(json.message || `请求失败：${res.status}`)
  }
  return json.data
}

async function login(body) {
  const res = await fetch(`${AUTH}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
    body: JSON.stringify(body)
  })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json.code !== 'BP00000') throw new Error(json.message || '登录失败')
  return json.data
}

async function me() {
  const res = await fetch(`${AUTH}/me`, { headers: { Authorization: `Bearer ${token()}` } })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json.code !== 'BP00000') throw new Error(json.message || '获取用户失败')
  return json.data
}

export const api = {
  login,
  me,
  myMenus: (sceneCode = 'GUARANTEE') => fetch(`${AUTH}/menus?sceneCode=${sceneCode}`, { headers: { Authorization: `Bearer ${token()}` } }).then(async r => {
    const j = await r.json().catch(() => ({}))
    if (!r.ok || j.code !== 'BP00000') throw new Error(j.message || '获取菜单失败')
    return j.data
  }),
  scenes: () => request('/scenes'),
  modes: (sceneCode) => request(`/scenes/${sceneCode}/business-modes`),
  templates: (sceneCode) => request(`/space-templates?sceneCode=${sceneCode}`),
  assetTypes: (sceneCode) => request(`/asset-types?sceneCode=${sceneCode}`),
  projects: () => request('/projects'),
  createProject: (body) => request('/projects', { method: 'POST', body: JSON.stringify(body) }),
  spaces: (projectId) => request(`/projects/${projectId}/spaces`),
  updateHouse: (projectId, houseId, body) => request(`/projects/${projectId}/houses/${houseId}/update`, { method: 'POST', body: JSON.stringify(body) }),
  createSpace: (projectId, body) => request(`/projects/${projectId}/spaces`, { method: 'POST', body: JSON.stringify(body) }),
  houses: (projectId) => request(`/projects/${projectId}/houses`),
  persons: (keyword = '') => request(`/persons?keyword=${encodeURIComponent(keyword)}`),
  createPerson: (body) => request('/persons', { method: 'POST', body: JSON.stringify(body) }),
  relations: (personId) => request(`/persons/${personId}/relations`),
  createRelation: (personId, body) => request(`/persons/${personId}/relations`, { method: 'POST', body: JSON.stringify(body) }),
  applications: (projectId) => request(`/guarantee/applications?projectId=${projectId}`),
  createApplication: (body) => request('/guarantee/applications', { method: 'POST', body: JSON.stringify(body) }),
  submitApplication: (id) => request(`/guarantee/applications/${id}/submit`, { method: 'POST' }),
  rejectApplication: (id, comment) => request(`/guarantee/applications/${id}/reject`, { method: 'POST', body: JSON.stringify({ comment }) }),
  returnApplication: (id, comment) => request(`/guarantee/applications/${id}/return`, { method: 'POST', body: JSON.stringify({ comment }) }),
  resubmitApplication: (id) => request(`/guarantee/applications/${id}/resubmit`, { method: 'POST' }),
  approveApplication: (id, comment) => request(`/guarantee/applications/${id}/approve`, { method: 'POST', body: JSON.stringify({ comment }) }),
  joinWaitlist: (id) => request(`/guarantee/applications/${id}/waitlist`, { method: 'POST' }),
  waitlist: (projectId) => request(`/guarantee/waitlist?projectId=${projectId}`),
  allocate: (waitlistId, houseId) => request(`/guarantee/waitlist/${waitlistId}/allocate`, { method: 'POST', body: JSON.stringify({ houseId }) }),
  contracts: (projectId) => request(`/guarantee/contracts?projectId=${projectId}`),
  createContract: (body) => request('/guarantee/contracts', { method: 'POST', body: JSON.stringify(body) }),
  submitContract: (id) => request(`/guarantee/contracts/${id}/submit`, { method: 'POST' }),
  approveContract: (id) => request(`/guarantee/contracts/${id}/approve`, { method: 'POST' }),
  activateContract: (id, reason) => request(`/guarantee/contracts/${id}/activate`, { method: 'POST', body: JSON.stringify({ reason }) }),
  withdrawContract: (id) => request(`/guarantee/contracts/${id}/withdraw`, { method: 'POST' }),
  discardContract: (id) => request(`/guarantee/contracts/${id}/discard`, { method: 'POST' }),
  generateBill: (contractId, body) => request(`/guarantee/contracts/${contractId}/bills`, { method: 'POST', body: JSON.stringify(body) }),
  deposit: (contractId) => request(`/guarantee/contracts/${contractId}/deposit`),
  payDeposit: (contractId, body) => request(`/guarantee/contracts/${contractId}/deposit/pay`, { method: 'POST', body: JSON.stringify(body) }),
  refundDeposit: (depositId, body) => request(`/guarantee/deposits/${depositId}/refund`, { method: 'POST', body: JSON.stringify(body) }),
  subsidies: (contractId) => request(`/guarantee/contracts/${contractId}/subsidies`),
  createSubsidy: (contractId, body) => request(`/guarantee/contracts/${contractId}/subsidies`, { method: 'POST', body: JSON.stringify(body) }),
  qualificationReviews: (contractId) => request(`/guarantee/contracts/${contractId}/qualification-reviews`),
  createQualificationReview: (contractId, body) => request(`/guarantee/contracts/${contractId}/qualification-reviews`, { method: 'POST', body: JSON.stringify(body) }),
  completeQualificationReview: (reviewId, body) => request(`/guarantee/qualification-reviews/${reviewId}/complete`, { method: 'POST', body: JSON.stringify(body) }),
  changes: (contractId) => request(`/guarantee/contracts/${contractId}/changes`),
  createChange: (contractId, body) => request(`/guarantee/contracts/${contractId}/changes`, { method: 'POST', body: JSON.stringify(body) }),
  submitChange: (changeId) => request(`/guarantee/contract-changes/${changeId}/submit`, { method: 'POST' }),
  approveChange: (changeId, body) => request(`/guarantee/contract-changes/${changeId}/approve`, { method: 'POST', body: JSON.stringify(body) }),
  rejectChange: (changeId, body) => request(`/guarantee/contract-changes/${changeId}/reject`, { method: 'POST', body: JSON.stringify(body) }),
  workflowTasks: (status = '') => request(`/workflow-tasks${status ? `?status=${status}` : ''}`),
  approveTask: (taskId, body) => request(`/workflow-tasks/${taskId}/approve`, { method: 'POST', body: JSON.stringify(body) }),
  rejectTask: (taskId, body) => request(`/workflow-tasks/${taskId}/reject`, { method: 'POST', body: JSON.stringify(body) }),
  workflowRecords: (taskId) => request(`/workflow-tasks/${taskId}/records`),
  migrationExceptions: (status = '') => request(`/migration/exceptions${status ? `?status=${status}` : ''}`),
  resolveMigrationException: (id, body) => request(`/migration/exceptions/${id}/resolve`, { method: 'POST', body: JSON.stringify(body) }),
  feeItems: (projectId) => request(`/guarantee/fee-items?projectId=${projectId}`),
  createFeeItem: (body) => request('/guarantee/fee-items', { method: 'POST', body: JSON.stringify(body) }),
  toggleFeeItem: (id, enabled) => request(`/guarantee/fee-items/${id}/toggle?enabled=${enabled}`, { method: 'POST' }),
  bills: (projectId) => request(`/billing/bills?projectId=${projectId}`),
  adjustBill: (billId, body) => request(`/billing/bills/${billId}/adjust`, { method: 'POST', body: JSON.stringify(body) }),
  contractBills: (contractId) => request(`/billing/contracts/${contractId}/bills`),
  payContract: (contractId, body) => request(`/billing/contracts/${contractId}/pay`, { method: 'POST', body: JSON.stringify(body) }),
  pay: (billId, body) => request(`/billing/bills/${billId}/pay`, { method: 'POST', body: JSON.stringify(body) }),
  payments: (projectId) => request(`/billing/payments?projectId=${projectId}`),
  paymentAllocations: (paymentId) => request(`/billing/payments/${paymentId}/allocations`),
  refundPayment: (paymentId, body) => request(`/billing/payments/${paymentId}/refund`, { method: 'POST', body: JSON.stringify(body) }),
  cohabitants: (contractId) => request(`/guarantee/contracts/${contractId}/cohabitants`),
  addCohabitant: (contractId, body) => request(`/guarantee/contracts/${contractId}/cohabitants`, { method: 'POST', body: JSON.stringify(body) }),
  removeCohabitant: (id) => request(`/guarantee/contract-cohabitants/${id}/remove`, { method: 'POST' }),
  files: (bizType, bizId) => request(`/files?bizType=${bizType}&bizId=${bizId}`),
  uploadFile: (bizType, bizId, file) => { const fd = new FormData(); fd.append('file', file); return request(`/files?bizType=${bizType}&bizId=${bizId}`, { method: 'POST', body: fd }) },
  downloadFile: async (id, name) => { const res = await fetch(`${BASE}/files/${id}/download`, { headers: { Authorization: `Bearer ${token()}` } }); if (!res.ok) throw new Error('下载失败'); const blob = await res.blob(); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name || 'download'; a.click(); URL.revokeObjectURL(a.href) },
  users: () => request('/users'),
  userRoles: () => request('/users/roles'),
  createUser: (body) => request('/users', { method: 'POST', body: JSON.stringify(body) }),
  updateUser: (id, body) => request(`/users/${id}/update`, { method: 'POST', body: JSON.stringify(body) }),
  userScopes: (id) => request(`/users/${id}/scopes`),
  updateUserScopes: (id, body) => request(`/users/${id}/scopes`, { method: 'POST', body: JSON.stringify(body) }),
  messages: () => request('/messages'),
  createMessage: (body) => request('/messages', { method: 'POST', body: JSON.stringify(body) }),
  readMessage: (id) => request(`/messages/${id}/read`, { method: 'POST' }),
  readAllMessages: () => request('/messages/read-all', { method: 'POST' }),
  openApps: () => request('/open-apps'),
  createOpenApp: (body) => request('/open-apps', { method: 'POST', body: JSON.stringify(body) }),
  toggleOpenApp: (id, enabled) => request(`/open-apps/${id}/toggle?enabled=${enabled}`, { method: 'POST' }),
  shortRentOrders: (projectId) => request(`/guarantee/short-rent-orders?projectId=${projectId}`),
  createShortRentOrder: (body) => request('/guarantee/short-rent-orders', { method: 'POST', body: JSON.stringify(body) }),
  updateShortRentStatus: (id, status) => request(`/guarantee/short-rent-orders/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  credits: (projectId) => request(`/guarantee/credits?projectId=${projectId}`),
  createCredit: (body) => request('/guarantee/credits', { method: 'POST', body: JSON.stringify(body) }),
  revokeCredit: (id) => request(`/guarantee/credits/${id}/revoke`, { method: 'POST' }),
  alerts: (projectId) => request(`/guarantee/alerts?projectId=${projectId}`),
  createAlert: (body) => request('/guarantee/alerts', { method: 'POST', body: JSON.stringify(body) }),
  handleAlert: (id, body) => request(`/guarantee/alerts/${id}/handle`, { method: 'POST', body: JSON.stringify(body) }),
  publicities: (projectId) => request(`/guarantee/publicities?projectId=${projectId}`),
  createPublicity: (body) => request('/guarantee/publicities', { method: 'POST', body: JSON.stringify(body) }),
  updatePublicityStatus: (id, status) => request(`/guarantee/publicities/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  complaints: (projectId, type) => request(`/guarantee/complaints?projectId=${projectId}${type ? '&type=' + type : ''}`),
  createComplaint: (body) => request('/guarantee/complaints', { method: 'POST', body: JSON.stringify(body) }),
  handleComplaint: (id, body) => request(`/guarantee/complaints/${id}/handle`, { method: 'POST', body: JSON.stringify(body) }),
  accessRecords: (projectId) => request(`/guarantee/access-records?projectId=${projectId}`),
  createAccessRecord: (body) => request('/guarantee/access-records', { method: 'POST', body: JSON.stringify(body) }),
  approveAccessRecord: (id, status) => request(`/guarantee/access-records/${id}/approve`, { method: 'POST', body: JSON.stringify({ status }) }),
  workOrders: (projectId) => request(`/guarantee/work-orders?projectId=${projectId}`),
  createWorkOrder: (body) => request('/guarantee/work-orders', { method: 'POST', body: JSON.stringify(body) }),
  updateWorkOrder: (id, body) => request(`/guarantee/work-orders/${id}/update`, { method: 'POST', body: JSON.stringify(body) }),
  meters: (projectId) => request(`/guarantee/meters?projectId=${projectId}`),
  createMeter: (body) => request('/guarantee/meters', { method: 'POST', body: JSON.stringify(body) }),
  meterReadings: (meterId) => request(`/guarantee/meters/${meterId}/readings`),
  readMeter: (meterId, body) => request(`/guarantee/meters/${meterId}/readings`, { method: 'POST', body: JSON.stringify(body) }),
  meterSummary: (projectId) => request(`/guarantee/meters/summary?projectId=${projectId}`),
  devices: (projectId) => request(`/devices?projectId=${projectId}`),
  importDevices: (file) => { const fd = new FormData(); fd.append('file', file); return request('/devices/import', { method: 'POST', body: fd }) },
  createDevice: (body) => request('/devices', { method: 'POST', body: JSON.stringify(body) }),
  bindDevice: (id, spaceId) => request(`/devices/${id}/bind`, { method: 'POST', body: JSON.stringify({ spaceId }) }),
  grants: (personId) => request(`/grants?personId=${personId}`),
  keyring: (personId) => request(`/persons/${personId}/keyring`),
  createGrant: (body) => request('/grants', { method: 'POST', body: JSON.stringify(body) }),
  revokeGrant: (grantId, reason = '') => request(`/grants/${grantId}/revoke`, { method: 'POST', body: JSON.stringify({ reason }) }),
  menus: (sceneCode) => request(`/menus?sceneCode=${sceneCode}`),
  roles: (sceneCode) => request(`/roles?sceneCode=${sceneCode}`),
  roleMenus: (roleId) => request(`/roles/${roleId}/menus`)
}
