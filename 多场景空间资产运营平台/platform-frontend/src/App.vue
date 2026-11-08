<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from './api'

const route = useRoute()
const router = useRouter()
const isLogin = computed(() => route.path === '/login')
const currentUser = computed(() => {
  try { return JSON.parse(localStorage.getItem('platformUser') || '{}') } catch { return {} }
})
const projects = ref([])
const currentProjectId = ref(localStorage.getItem('platformProjectId') || '')

onMounted(async () => {
  try {
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

function logout() {
  localStorage.removeItem('platformToken')
  localStorage.removeItem('platformUser')
  router.replace('/login')
}
const title = computed(() => route.meta.title || '工作台')
const nav = [
  { to: '/', label: '工作台', icon: '◈' },
  { to: '/projects', label: '项目与资产', icon: '▦' },
  { to: '/applications', label: '申请与轮候', icon: '☷' },
  { to: '/contracts', label: '合同与租赁', icon: '▤' },
  { to: '/changes', label: '合同变更', icon: '⇄' },
  { to: '/billing', label: '收费与账务', icon: '¥' },
  { to: '/deposits', label: '押金与补贴', icon: '◫' },
  { to: '/devices', label: '设备与授权', icon: '⌘' },
  { to: '/audit', label: '审批中心', icon: '✓' },
  { to: '/menus', label: '菜单与角色', icon: '☰' }
]
</script>

<template>
  <RouterView v-if="isLogin" />
  <div v-else class="shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">MS</div>
        <div>
          <div class="brand-title">多场景空间资产</div>
          <div class="brand-sub">运营平台 · 保障房场景</div>
        </div>
      </div>
      <nav class="nav">
        <RouterLink v-for="item in nav" :key="item.to" :to="item.to" class="nav-item">
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-foot">
        <span class="dot online"></span>
        平台服务 8090
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <div>
          <h1>{{ title }}</h1>
          <p>租户 350600 · GUARANTEE 场景</p>
        </div>
        <div class="top-actions row">
          <select v-model="currentProjectId" @change="switchProject" style="max-width:260px">
            <option value="">选择项目</option>
            <option v-for="p in projects" :key="p.id" :value="String(p.id)">{{ p.orgName }}（{{ p.orgCode }}）</option>
          </select>
          <span class="pill">{{ currentUser.displayName || currentUser.username || '用户' }}</span>
          <button class="sm" @click="logout">退出</button>
        </div>
      </header>
      <section class="content">
        <RouterView />
      </section>
    </main>
  </div>
</template>
