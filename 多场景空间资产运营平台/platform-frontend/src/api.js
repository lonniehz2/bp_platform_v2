const BASE = '/api/v1/platform'
const TENANT = '350600'

async function request(path, options = {}) {
  const headers = { 'X-Tenant-Id': TENANT, ...(options.headers || {}) }
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json; charset=utf-8'
  }
  const res = await fetch(BASE + path, { ...options, headers })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || json.code !== 'BP00000') {
    throw new Error(json.message || `请求失败：${res.status}`)
  }
  return json.data
}

export const api = {
  scenes: () => request('/scenes'),
  modes: (sceneCode) => request(`/scenes/${sceneCode}/business-modes`),
  templates: (sceneCode) => request(`/space-templates?sceneCode=${sceneCode}`),
  assetTypes: (sceneCode) => request(`/asset-types?sceneCode=${sceneCode}`),
  projects: () => request('/projects'),
  createProject: (body) => request('/projects', { method: 'POST', body: JSON.stringify(body) }),
  spaces: (projectId) => request(`/projects/${projectId}/spaces`),
  houses: (projectId) => request(`/projects/${projectId}/houses`),
  persons: (keyword = '') => request(`/persons?keyword=${encodeURIComponent(keyword)}`),
  createPerson: (body) => request('/persons', { method: 'POST', body: JSON.stringify(body) }),
  applications: (projectId) => request(`/guarantee/applications?projectId=${projectId}`),
  createApplication: (body) => request('/guarantee/applications', { method: 'POST', body: JSON.stringify(body) }),
  submitApplication: (id) => request(`/guarantee/applications/${id}/submit`, { method: 'POST' }),
  approveApplication: (id, comment) => request(`/guarantee/applications/${id}/approve`, { method: 'POST', body: JSON.stringify({ comment }) }),
  joinWaitlist: (id) => request(`/guarantee/applications/${id}/waitlist`, { method: 'POST' }),
  waitlist: (projectId) => request(`/guarantee/waitlist?projectId=${projectId}`),
  allocate: (waitlistId, houseId) => request(`/guarantee/waitlist/${waitlistId}/allocate`, { method: 'POST', body: JSON.stringify({ houseId }) }),
  contracts: (projectId) => request(`/guarantee/contracts?projectId=${projectId}`),
  createContract: (body) => request('/guarantee/contracts', { method: 'POST', body: JSON.stringify(body) }),
  generateBill: (contractId, body) => request(`/guarantee/contracts/${contractId}/bills`, { method: 'POST', body: JSON.stringify(body) }),
  bills: (projectId) => request(`/billing/bills?projectId=${projectId}`),
  pay: (billId, body) => request(`/billing/bills/${billId}/pay`, { method: 'POST', body: JSON.stringify(body) }),
  payments: (projectId) => request(`/billing/payments?projectId=${projectId}`),
  devices: (projectId) => request(`/devices?projectId=${projectId}`),
  createDevice: (body) => request('/devices', { method: 'POST', body: JSON.stringify(body) }),
  grants: (personId) => request(`/grants?personId=${personId}`),
  createGrant: (body) => request('/grants', { method: 'POST', body: JSON.stringify(body) }),
  menus: (sceneCode) => request(`/menus?sceneCode=${sceneCode}`),
  roles: (sceneCode) => request(`/roles?sceneCode=${sceneCode}`),
  roleMenus: (roleId) => request(`/roles/${roleId}/menus`)
}
