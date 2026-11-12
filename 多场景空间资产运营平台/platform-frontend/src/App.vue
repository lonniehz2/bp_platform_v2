<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from './api'
import { getMenus, setMenus } from './permissions'
import { mode, toggleMode } from './ui'
import { setLocale } from './i18n'
import { currentScene, scenePath, sceneOfPath } from './scene'
import { navGroups, navItems } from './navConfig'
import SearchSelect from './components/SearchSelect.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'

const route = useRoute()
const router = useRouter()
const { t, te, locale } = useI18n()
const sceneCode = computed(() => sceneOfPath(route.path))
const loadedScene = ref('')

const isLogin = computed(() => route.path === '/login')
const isPublicPage = computed(() => route.meta?.public === true)
const collapsed = ref(localStorage.getItem('platformSidebar') === '1')
const projects = ref([])
const currentProjectId = ref(localStorage.getItem('platformProjectId') || '')
const allowedMenus = ref(getMenus())
const menuTree = ref([])
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

const openGroups = ref(new Set())

const visibleGroups = computed(() => navGroups.map(g => ({
  ...g,
  items: g.items.filter(item => allowedMenus.value.length === 0 || allowedMenus.value.includes(item.menu))
})).filter(g => g.items.length > 0))
const groupIconMap = {
  group_workbench: '◈', group_application: '☷', group_contract: '▤',
  group_finance: '¥', group_asset: '▦', group_service: '⚒', group_access: '⌘',
  group_risk: '⚠', group_data: '▥', group_system: '☰'
}
const sidebarGroups = computed(() => {
  if (!menuTree.value.length) return visibleGroups.value
  return menuTree.value.map(g => ({
    key: g.menuCode,
    label: te(`group.${g.menuCode.replace('group_', '')}`) ? t(`group.${g.menuCode.replace('group_', '')}`) : g.menuName,
    icon: groupIconMap[g.menuCode] || '•',
    items: (g.children || []).map(p => ({
      to: p.route,
      key: p.menuCode,
      label: te(`nav.${p.menuCode}`) ? t(`nav.${p.menuCode}`) : p.menuName,
      icon: '·'
    }))
  })).filter(g => g.items.length)
})

const currentGroupKey = computed(() => {
  const path = route.path
  const group = sidebarGroups.value.find(g => g.items.some(item =>
    path === scenePath(item.to) || path.startsWith(scenePath(item.to) + '/')))
  return group ? group.key : ''
})

function isGroupOpen(key) {
  return openGroups.value.has(key)
}

function isCurrentGroup(group) {
  return currentGroupKey.value === group.key
}

function toggleGroup(key) {
  const next = new Set()
  if (!openGroups.value.has(key)) next.add(key)
  openGroups.value = next
}

watch(currentGroupKey, (key) => {
  if (key) openGroups.value = new Set([key])
}, { immediate: true })

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
  '/imports': 'nav.batchImport',
  '/reports': 'nav.reports',
  '/meters': 'nav.meter',
  '/energy': 'nav.energy',
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
  '/rbac': 'nav.rbac',
  '/menus': 'nav.config',
  '/migration-exceptions': 'nav.migration',
  '/help': 'nav.help'
}
for (const item of navItems) {
  if (!titleKey[item.to]) titleKey[item.to] = 'nav.' + item.key
}
const title = computed(() => t(route.meta?.titleKey || titleKey[route.path] || 'nav.dashboard'))
watch(title, value => { document.title = value }, { immediate: true })

watch([() => route.path, sceneCode], async () => {
  if (route.path === '/login' || !localStorage.getItem('platformToken')) return
  if (loadedScene.value !== sceneCode.value) {
    menuTree.value = []
    loadedScene.value = ''
  }
  await loadSceneMenus()
})

async function loadSceneMenus() {
  if (!localStorage.getItem('platformToken') || loadedScene.value === sceneCode.value) return
  const scene = sceneCode.value
  try {
    const [menus, tree] = await Promise.all([api.myMenus(scene), api.myMenuTree(scene)])
    setMenus(menus)
    allowedMenus.value = menus
    menuTree.value = tree || []
    loadedScene.value = scene
  } catch {}
}

onMounted(async () => {
  try {
    await loadSceneMenus()
    projects.value = await api.projects()
    if (projects.value.length) {
      const exists = projects.value.some(p => String(p.id) === String(currentProjectId.value))
      if (!currentProjectId.value || !exists) {
        const demo = projects.value.find(p => p.orgCode === 'DEMO_PROJECT')
        const best = demo || projects.value.slice().sort((a, b) =>
          ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
          ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
        )[0]
        currentProjectId.value = String(best.id)
        localStorage.setItem('platformProjectId', currentProjectId.value)
      }
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
  if (!pwd.oldPassword || pwd.newPassword.length < 6) { pwdError.value = t('shell.pwdRequired'); return }
  if (pwd.newPassword !== pwd.confirm) { pwdError.value = t('shell.pwdMismatch'); return }
  try {
    await api.changePassword({ oldPassword: pwd.oldPassword, newPassword: pwd.newPassword })
    pwdOpen.value = false
    pwd.oldPassword = ''; pwd.newPassword = ''; pwd.confirm = ''
    alert(t('shell.pwdChanged'))
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
  <RouterView v-if="isPublicPage" />
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
        <div v-for="g in sidebarGroups" :key="g.key" class="nav-group" :class="{ active: isCurrentGroup(g) }">
          <button class="nav-group-head" :class="{ active: isCurrentGroup(g) }" @click="toggleGroup(g.key)" :title="g.label || t(g.labelKey)">
            <span class="nav-group-icon">{{ g.icon }}</span>
            <span class="nav-label">{{ g.label || t(g.labelKey) }}</span>
            <span class="nav-label nav-group-arrow">{{ isGroupOpen(g.key) ? '⌄' : '›' }}</span>
          </button>
          <div v-show="isGroupOpen(g.key)" class="nav-group-items">
            <RouterLink v-for="item in g.items" :key="item.to" :to="scenePath(item.to)" class="nav-item">
              <span class="nav-icon">{{ item.icon }}</span>
              <span class="nav-label">{{ item.label || t('nav.' + item.key) }}</span>
            </RouterLink>
          </div>
        </div>
      </nav>
      <div class="sidebar-foot">
        <span class="dot online"></span>
        API 8090 · v0.1
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <button class="ghost sm" @click="toggleSidebar" :title="t('shell.collapse')">☰</button>
        <div class="page-heading">
          <h1>{{ title }}</h1>
          <p>{{ currentUser.displayName || currentUser.username || 'admin' }} · {{ currentUser.tenantId || '350600' }}</p>
        </div>
        <div class="top-actions">
          <SearchSelect
            v-model="currentProjectId"
            :options="projects"
            label-key="orgName"
            sublabel-key="orgCode"
            value-key="id"
            :placeholder="t('shell.selectProject')"
            class="project-picker"
            @change="switchProject"
          />
          <a v-if="isAdmin" class="admin-link" :href="legacyAdminUrl" target="_blank" rel="noopener">{{ t('common.admin') }}</a>
          <button class="ghost sm" @click="switchLocale">{{ locale === 'zh-CN' ? 'EN' : 'ZH' }}</button>
          <button class="ghost sm" @click="toggleMode">{{ mode === 'dark' ? '☀' : '☾' }}</button>
          <button class="sm" @click="pwdOpen = true">{{ t('shell.changePwd') }}</button>
          <button class="sm" @click="logout">{{ t('common.logout') }}</button>
        </div>
      </header>
      <section class="content">
        <RouterView />
      </section>
    </main>

    <div v-if="pwdOpen" class="modal-mask" @click.self="pwdOpen = false">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('shell.changePwd') }}</h2><button class="sm" @click="pwdOpen = false">{{ t('shell.close') }}</button></div>
        <div v-if="pwdError" class="error">{{ pwdError }}</div>
        <div class="field"><label>{{ t('shell.oldPwd') }}</label><input v-model="pwd.oldPassword" type="password" /></div>
        <div class="field"><label>{{ t('shell.newPwd') }}</label><input v-model="pwd.newPassword" type="password" /></div>
        <div class="field"><label>{{ t('shell.confirmPwd') }}</label><input v-model="pwd.confirm" type="password" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" @click="changePassword">{{ t('shell.save') }}</button></div>
      </div>
    </div>
    <ConfirmDialog />
  </div>
</template>
