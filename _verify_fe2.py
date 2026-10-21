# -*- coding: utf-8 -*-
"""生成前端：API 封装 + 状态 + 路由 + 布局"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

F['src/api/modules.js'] = '''import req from './request'

/** 认证 */
export const authApi = {
  login: (data) => req.post('/auth/login', data),
  logout: () => req.post('/auth/logout'),
  me: () => req.get('/auth/me')
}

/** 组织与房源 */
export const orgApi = {
  page: (params) => req.get('/orgs', { params }),
  tree: (params) => req.get('/orgs/tree', { params })
}

export const houseApi = {
  page: (params) => req.get('/houses', { params }),
  get: (id) => req.get(`/houses/${id}`)
}

/** 申请与审核 */
export const applicationApi = {
  page: (params) => req.get('/applications', { params }),
  get: (id) => req.get(`/applications/${id}`),
  create: (data) => req.post('/applications', data),
  submit: (id) => req.post(`/applications/${id}/submit`),
  accept: (id) => req.post(`/applications/${id}/accept`),
  review: (id, data) => req.post(`/applications/${id}/review`, data),
  records: (id) => req.get(`/applications/${id}/records`)
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
  rank: (batchId) => req.post(`/waitlist/rank?batchId=${batchId}`)
}

/** 配租批次与摇号 */
export const allocationApi = {
  batches: (params) => req.get('/allocation/batches', { params }),
  createBatch: (data) => req.post('/allocation/batches', data),
  addHouses: (batchId, houseIds) =>
    req.post(`/allocation/batches/${batchId}/houses`, houseIds),
  lottery: (batchId, seed) =>
    req.post(`/allocation/batches/${batchId}/lottery?seed=${seed ?? ''}`),
  results: (batchId) => req.get(`/allocation/batches/${batchId}/results`),
  allocations: (params) => req.get('/allocations', { params }),
  sign: (id, data) => req.post(`/allocations/${id}/sign`, data)
}

/** 合同 */
export const contractApi = {
  page: (params) => req.get('/contracts', { params }),
  get: (id) => req.get(`/contracts/${id}`)
}

/** 账务 */
export const financeApi = {
  bills: (params) => req.get('/bills', { params }),
  bill: (id) => req.get(`/bills/${id}`),
  generate: (data) => req.post('/bills/generate', data),
  allocate: (paymentId, billId, amount) =>
    req.post('/payments/allocate', { paymentId, billId, amount }),
  payments: (params) => req.get('/payments', { params })
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
  metrics: (orgId) => req.get('/rpt/metrics/current', { params: { orgId } })
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
  send: (data) => req.post('/messages/send', data)
}
'''

F['src/store/auth.js'] = '''import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/modules'
import { setToken, setTenant, getToken } from '@/api/request'

/**
 * 登录态与权限。
 *
 * 权限码来自后端 /auth/me 的 permissions；admin=true 时拥有全部权限。
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref(getToken())
  const user = ref(null)
  const permissions = ref([])
  const admin = ref(false)

  const loggedIn = computed(() => !!token.value)
  const displayName = computed(
    () => user.value?.realName || user.value?.username || '未登录'
  )

  async function login({ tenantId, username, password }) {
    setTenant(tenantId)
    const data = await authApi.login({ tenantId, username, password })
    token.value = data.token
    setToken(data.token)
    admin.value = !!data.admin
    await loadMe()
    return data
  }

  async function loadMe() {
    const me = await authApi.me()
    user.value = me
    permissions.value = me.permissions || []
    admin.value = !!me.admin
    return me
  }

  /** 是否拥有某权限（admin 直接放行）。 */
  function has(code) {
    if (admin.value) return true
    if (!code) return true
    return permissions.value.includes(code)
  }

  function logout() {
    token.value = ''
    user.value = null
    permissions.value = []
    admin.value = false
    setToken('')
  }

  return { token, user, permissions, admin, loggedIn, displayName,
           login, loadMe, has, logout }
})
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件（API/状态）' % count)
