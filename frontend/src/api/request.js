import axios from 'axios'
import { ElMessage } from 'element-plus'

/**
 * 统一请求封装。
 *
 * - 自动带上 Authorization（不透明令牌）与 X-Tenant-Id
 * - 统一解包后端 R<T>：code === 'BP00000' 视为成功
 * - 401 自动回登录页；403 提示无权限
 */
const service = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

const TOKEN_KEY = 'bp_token'
const TENANT_KEY = 'bp_tenant'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}

export function getTenant() {
  return localStorage.getItem(TENANT_KEY) || '350600'
}

export function setTenant(t) {
  localStorage.setItem(TENANT_KEY, t || '350600')
}

service.interceptors.request.use((cfg) => {
  const token = getToken()
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  cfg.headers['X-Tenant-Id'] = getTenant()
  return cfg
})

service.interceptors.response.use(
  (resp) => {
    const body = resp.data
    // 非 R 结构（如文件流）直接返回
    if (!body || typeof body !== 'object' || body.code === undefined) return body
    if (body.code === 'BP00000') return body.data
    ElMessage.error(body.message || `请求失败（${body.code}）`)
    return Promise.reject(body)
  },
  (err) => {
    const status = err.response?.status
    const body = err.response?.data
    if (status === 401) {
      ElMessage.error('登录已失效，请重新登录')
      setToken('')
      setTimeout(() => { window.location.hash = '#/login' }, 300)
    } else if (status === 403) {
      ElMessage.error(body?.message || '无权限访问该功能')
    } else {
      ElMessage.error(body?.message || err.message || '网络异常')
    }
    return Promise.reject(err)
  }
)

export default service
