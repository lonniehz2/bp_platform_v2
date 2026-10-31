import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/modules'
import { setToken, setTenant, getToken } from '@/api/request'
import { setLocale } from '@/i18n'

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
    const chosen = localStorage.getItem('bp_locale')
    if (chosen) authApi.saveLocale(chosen).catch(() => {})
    return data
  }

  async function loadMe() {
    const me = await authApi.me()
    user.value = me
    permissions.value = me.permissions || []
    admin.value = !!me.admin
    if (me.locale && !localStorage.getItem('bp_locale')) setLocale(me.locale)
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
