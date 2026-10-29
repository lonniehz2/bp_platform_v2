import axios from 'axios'
import { ElMessage } from 'element-plus'

const KEY = 'bp.operator.token'
const NAME = 'bp.operator.name'

export function getOperatorToken() { return localStorage.getItem(KEY) || '' }
export function setOperatorToken(t) {
  if (t) localStorage.setItem(KEY, t)
  else localStorage.removeItem(KEY)
}
export function getOperatorName() { return localStorage.getItem(NAME) || '' }
export function setOperatorName(n) {
  if (n) localStorage.setItem(NAME, n)
  else localStorage.removeItem(NAME)
}

const http = axios.create({ baseURL: '/api/v1', timeout: 30000 })

http.interceptors.request.use((cfg) => {
  const t = getOperatorToken()
  if (t) cfg.headers['X-Operator-Token'] = t
  return cfg
})

http.interceptors.response.use(
  (res) => {
    const r = res.data
    if (r && r.code === 'BP00000') return r.data
    ElMessage.error((r && r.message) || '请求失败')
    return Promise.reject(new Error((r && r.message) || '请求失败'))
  },
  (err) => {
    const status = err?.response?.status
    const msg = err?.response?.data?.message || err.message || '网络异常'
    if (status === 401) {
      setOperatorToken('')
      if (!location.hash.startsWith('#/platform-admin/login')) {
        location.hash = '#/platform-admin/login'
      }
    }
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export const operatorApi = {
  login: (data) => http.post('/platform-admin/auth/login', data),
  changePassword: (data) => http.post('/platform-admin/auth/change-password', data),
  logout: () => http.post('/platform-admin/auth/logout'),
  platforms: (params) => http.get('/platform-admin/platforms', { params }),
  platform: (id) => http.get('/platform-admin/platforms/' + id),
  createPlatform: (data) => http.post('/platform-admin/platforms', data),
  updatePlatform: (id, data) => http.put('/platform-admin/platforms/' + id, data),
  enable: (id) => http.post('/platform-admin/platforms/' + id + '/enable'),
  disable: (id) => http.post('/platform-admin/platforms/' + id + '/disable'),
  archive: (id) => http.post('/platform-admin/platforms/' + id + '/archive'),
  restore: (id) => http.post('/platform-admin/platforms/' + id + '/restore'),
  admins: (id) => http.get('/platform-admin/platforms/' + id + '/admins'),
  createAdmin: (id, data) => http.post('/platform-admin/platforms/' + id + '/admins', data),
  resetPwd: (id, uid) => http.post('/platform-admin/platforms/' + id + '/admins/' + uid + '/reset-password'),
  enableAdmin: (id, uid) => http.post('/platform-admin/platforms/' + id + '/admins/' + uid + '/enable'),
  disableAdmin: (id, uid) => http.post('/platform-admin/platforms/' + id + '/admins/' + uid + '/disable'),
  unlockAdmin: (id, uid) => http.post('/platform-admin/platforms/' + id + '/admins/' + uid + '/unlock'),
  audits: (params) => http.get('/platform-admin/audits', { params })
}

export default http
