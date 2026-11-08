<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from './api'
import { getMenus, setMenus } from './permissions'
import { mode, toggleMode } from './ui'
import { setLocale } from './i18n'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()

const isLogin = computed(() => route.path === '/login')
const collapsed = ref(localStorage.getItem('platformSidebar') === '1')
const projects = ref([])
const currentProjectId = ref(localStorage.getItem('platformProjectId') || '')
const allowedMenus = ref(getMenus())
const pwdOpen = ref(false)
function toggleSidebar() {
  collapsed.value = !collapsed.value
  localStorage.setItem('platformSidebar', collapsed.value ? '1' : '0')
}
const pwdError = ref('')
const pwd = reactive({ oldPassword: '', newPassword: '', confirm: '' })
const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('platformUser') || '{}') } catch { return {} }
})
const isAdmin = computed(() => {
  const roles = currentUser.value.roles || []
  return currentUser.value.username === 'admin' || roles.includes('GUARANTEE_ADMIN')
})
const legacyAdminUrl = computed(() => `${location.protocol}//${location.hostname}:8080/platform-admin`)

const nav = [
  { to: '/', key: 'dashboard', menu: 'dashboard', icon: '◈' },
  { to: '/search', key: 'search', menu: 'search', icon: '⌕' },
  { to: '/projects', key: 'asset', menu: 'asset', icon: '▦' },
  { to: '/persons', key: 'person', menu: 'person', icon: '♙' },
  { to: '/applications', key: 'application', menu: 'application', icon: '☷' },
  { to: '/contracts', key: 'contract', menu: 'contract', icon: '▤' },
  { to: '/changes', key: 'changes', menu: 'contract', icon: '⇄' },
  { to: '/qualification', key: 'qualification', menu: 'contract', icon: '◎' },
  { to: '/billing', key: 'billing', menu: 'billing', icon: '¥' },
  { to: '/deposits', key: 'deposits', menu: 'billing', icon: '◫' },
  { to: '/arrears', key: 'arrears', menu: 'billing', icon: '!' },
  { to: '/cashflow', key: 'cashflow', menu: 'billing', icon: '↕' },
  { to: '/fee-items', key: 'fee', menu: 'billing', icon: '≡' },
  { to: '/reports', key: 'reports', menu: 'billing', icon: '▤' },
  { to: '/meters', key: 'meter', menu: 'asset', icon: '◉' },
  { to: '/devices', key: 'device', menu: 'device', icon: '⌘' },
  { to: '/work-orders', key: 'service', menu: 'service', icon: '⚒' },
  { to: '/access-records', key: 'access', menu: 'access', icon: '⌂' },
  { to: '/complaints', key: 'complaint', menu: 'complaint', icon: '☏' },
  { to: '/publicities', key: 'publicity', menu: 'publicity', icon: '▣' },
  { to: '/alerts', key: 'alert', menu: 'alert', icon: '⚠' },
  { to: '/credits', key: 'credit', menu: 'credit', icon: '✖' },
  { to: '/short-rent-orders', key: 'shortrent', menu: 'shortrent', icon: '⌂' },
  { to: '/house-calendar', key: 'calendar', menu: 'calendar', icon: '▦' },
  { to: '/open-apps', key: 'open', menu: 'open', icon: '⇄' },
  { to: '/messages', key: 'message', menu: 'message', icon: '✉' },
  { to: '/gov-report', key: 'gov', menu: 'gov', icon: '⇪' },
  { to: '/audit', key: 'audit', menu: 'audit', icon: '✓' },
  { to: '/users', key: 'users', menu: 'config', icon: '♟' },
  { to: '/menus', key: 'config', menu: 'config', icon: '☰' },
  { to: '/migration-exceptions', key: 'migration', menu: 'system', icon: '!' },
  { to: '/help', key: 'help', menu: 'help', icon: '?' }
]
const visibleNav = computed(() => nav.filter(item => allowedMenus.value.length === 0 || allowedMenus.value.includes(item.menu)))

const titleKey = {
  '/': 'nav.dashboard',
  '/search': 'nav.search',
  '/projects': 'nav.asset',
  '/applications': 'nav.application',
  '/contracts': 'nav.contract',
  '/changes': 'nav.changes',
  '/qualification': 'nav.qualification',
  '/billing': 'nav.billing',
  '/deposits': 'nav.deposits',
  '/arrears': 'nav.arrears',
  '/cashflow': 'nav.cashflow',
  '/fee-items': 'nav.fee',
  '/reports': 'nav.reports',
  '/meters': 'nav.meter',
  '/devices': 'nav.device',
  '/work-orders': 'nav.service',
  '/access-records': 'nav.access',
  '/complaints': 'nav.complaint',
  '/publicities': 'nav.publicity',
  '/alerts': 'nav.alert',
  '/credits': 'nav.credit',
  '/short-rent-orders': 'nav.shortrent',
  '/house-calendar': 'nav.calendar',
  '/open-apps': 'nav.open',
  '/messages': 'nav.message',
  '/gov-report': 'nav.gov',
  '/audit': 'nav.audit',
  '/users': 'nav.users',
  '/menus': 'nav.config',
  '/migration-exceptions': 'nav.migration',
  '/help': 'nav.help'
}
const title = computed(() => t(titleKey[route.path] || 'nav.dashboard'))

onMounted(async () => {
  try {
    if (localStorage.getItem('platformToken') && allowedMenus.value.length === 0) {
      try {
        const menus = await api.myMenus('GUARANTEE')
        setMenus(menus)
        allowedMenus.value = menus
      } catch {}
    }
    projects.value = await api.projects()
    if (!currentProjectId.value && projects.value.length) {
      const best = projects.value.slice().sort((a, b) =>
        ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
        ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
      )[0]
      currentProjectId.value = String(best.id)
      localStorage.setItem('platformProjectId', currentProjectId.value)
    }
  } catch {}
})

function switchProject() {
  localStorage.setItem('platformProjectId', currentProjectId.value)
  window.location.reload()
}

function switchLocale() {
  setLocale(locale.value === 'zh-CN' ? 'en-US' : 'zh-CN')
}

async function changePassword() {
  pwdError.value = ''
  if (!pwd.oldPassword || pwd.newPassword.length < 6) { pwdError.value = '请输入原密码，新密码至少 6 位'; return }
  if (pwd.newPassword !== pwd.confirm) { pwdError.value = '两次新密码不一致'; return }
  try {
    await api.changePassword({ oldPassword: pwd.oldPassword, newPassword: pwd.newPassword })
    pwdOpen.value = false
    pwd.oldPassword = ''; pwd.newPassword = ''; pwd.confirm = ''
    alert('密码已修改')
  } catch (e) { pwdError.value = e.message }
}

function logout() {
  localStorage.removeItem('platformToken')
  localStorage.removeItem('platformUser')
  localStorage.removeItem('platformMenus')
  router.replace('/login')
}
</script>

<template>
  <RouterView v-if="isLogin" />
  <div v-else class="shell">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand">
        <div class="brand-mark">MS</div>
        <div class="brand-text">
          <div class="brand-title">{{ t('login.brand') }}</div>
          <div class="brand-sub">{{ t('login.platform') }}</div>
        </div>
      </div>
      <nav class="nav">
        <RouterLink v-for="item in visibleNav" :key="item.to" :to="item.to" class="nav-item">
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ t('nav.' + item.key) }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-foot">
        <span class="dot online"></span>
        API 8090 · v0.1
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <button class="ghost sm" @click="toggleSidebar" title="折叠菜单">☰</button>
        <div class="page-heading">
          <h1>{{ title }}</h1>
          <p>{{ currentUser.displayName || currentUser.username || 'admin' }} · {{ currentUser.tenantId || '350600' }}</p>
        </div>
        <div class="top-actions">
          <select v-model="currentProjectId" @change="switchProject" class="project-select">
            <option value="">{{ t('common.project') }}</option>
            <option v-for="p in projects" :key="p.id" :value="String(p.id)">{{ p.orgName }}（{{ p.orgCode }}）</option>
          </select>
          <a v-if="isAdmin" class="admin-link" :href="legacyAdminUrl" target="_blank" rel="noopener">平台管理</a>
          <button class="ghost sm" @click="switchLocale">{{ locale === 'zh-CN' ? 'EN' : '中' }}</button>
          <button class="ghost sm" @click="toggleMode">{{ mode === 'dark' ? '☀' : '☾' }}</button>
          <button class="sm" @click="pwdOpen = true">修改密码</button>
          <button class="sm" @click="logout">{{ t('common.logout') }}</button>
        </div>
      </header>
      <section class="content">
        <RouterView />
      </section>
    </main>

    <div v-if="pwdOpen" class="modal-mask" @click.self="pwdOpen = false">
      <div class="modal">
        <div class="panel-head"><h2>修改密码</h2><button class="sm" @click="pwdOpen = false">关闭</button></div>
        <div v-if="pwdError" class="error">{{ pwdError }}</div>
        <div class="field"><label>原密码</label><input v-model="pwd.oldPassword" type="password" /></div>
        <div class="field"><label>新密码（至少 6 位）</label><input v-model="pwd.newPassword" type="password" /></div>
        <div class="field"><label>确认新密码</label><input v-model="pwd.confirm" type="password" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" @click="changePassword">保存</button></div>
      </div>
    </div>
  </div>
</template>
