import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getLocale } from '@/i18n'
import { enumLabel } from '@/constants/enums'

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

const LABEL_BASE = /(Status|Type|Source|Result|Level|Mode|Category|Stage|Sla|Kind|Channel|Priority|Scope|Cycle|Method)$/

/**
 * 英文模式下，后端返回的 xxxLabel 往往是中文。
 * 若同一行同时有原始枚举码（如 status + statusLabel），用前端字典覆盖标签值，
 * 这样所有使用 row.statusLabel 的页面都会自动显示英文。
 */
function localizeLabelFields(value) {
  if (getLocale() !== 'en-US' || !value || typeof value !== 'object') return value
  if (Array.isArray(value)) {
    value.forEach(localizeLabelFields)
    return value
  }
  for (const key of Object.keys(value)) {
    const child = value[key]
    if (child && typeof child === 'object') {
      localizeLabelFields(child)
      continue
    }
    if (!key.endsWith('Label')) continue
    const base = key.slice(0, -5)
    if (!LABEL_BASE.test(base)) continue
    const raw = value[base]
    if (typeof raw !== 'string' || !raw) continue
    value[key] = enumLabel(base, raw)
  }
  return value
}

service.interceptors.request.use((cfg) => {
  const token = getToken()
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  cfg.headers['X-Tenant-Id'] = getTenant()
  cfg.headers['X-Locale'] = getLocale()
  cfg.headers['Accept-Language'] = getLocale()
  return cfg
})

service.interceptors.response.use(
  (resp) => {
    const body = resp.data
    // 非 R 结构（如文件流）直接返回
    if (!body || typeof body !== 'object' || body.code === undefined) return body
    if (body.code === 'BP00000') return localizeLabelFields(body.data)
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
