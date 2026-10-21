# -*- coding: utf-8 -*-
"""双风格布局：风格1（宽侧栏分组）+ 风格2（图标窄栏），可切换且内容共用"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'
LAY = os.path.join(FE, 'layout')

# ================= ① 风格状态（持久化） =================
STORE = '''import { reactive, watch } from 'vue'

const KEY = 'bp.ui.style'

/**
 * 布局风格：
 *   classic —— 风格1：宽侧栏 + 分组二级菜单（传统后台，信息密度高）
 *   rail    —— 风格2：图标窄栏 + 二级面板（参考系统样式，视觉更轻）
 *
 * 两种风格共用同一套路由与页面组件，切换只影响外壳，**内容完全同步**。
 */
function read() {
  try {
    const v = localStorage.getItem(KEY)
    return v === 'classic' || v === 'rail' ? v : 'rail'
  } catch (e) {
    return 'rail'
  }
}

export const uiState = reactive({ style: read() })

watch(() => uiState.style, (v) => {
  try { localStorage.setItem(KEY, v) } catch (e) { /* ignore */ }
})

export function setStyle(v) {
  uiState.style = v === 'classic' ? 'classic' : 'rail'
}

export function toggleStyle() {
  setStyle(uiState.style === 'rail' ? 'classic' : 'rail')
}
'''
io.open(os.path.join(LAY, 'uiState.js'), 'w', encoding='utf-8').write(STORE)
print('  ✓ layout/uiState.js（风格状态 + localStorage 持久化）')

# ================= ② 共用菜单逻辑 =================
MENUS = '''import { computed } from 'vue'
import { menuRoutes } from '@/router'
import { useAuthStore } from '@/store/auth'

/** 一级分组顺序（两种风格共用） */
export const GROUP_ORDER = [
  '仪表盘', '会员', '线索', '房源', '合同', '财务', '管理后台', '更多'
]

export const GROUP_ICON = {
  仪表盘: 'Odometer',
  会员: 'User',
  线索: 'Tickets',
  房源: 'OfficeBuilding',
  合同: 'Document',
  财务: 'Money',
  管理后台: 'Setting',
  更多: 'Grid'
}

/** 组内业务顺序 */
const MENU_RANK = {
  '/dashboard': 1,
  '/persons': 10,
  '/applications': 20, '/waitlist': 21, '/publicities': 22, '/annual-reviews': 23,
  '/houses': 30, '/spaces': 31, '/house-calendar': 32, '/short-rent': 33,
  '/devices': 34, '/access': 35, '/keyring': 36, '/grants': 37,
  '/contracts': 40, '/contract-changes': 41, '/exchanges': 42,
  '/terminations': 43, '/allocations': 44,
  '/fee-items': 50, '/bills': 51, '/deposits': 52, '/arrears': 53,
  '/subsidies': 54, '/cashflow': 55, '/reports': 56,
  '/orgs': 60, '/rbac': 61, '/sys': 62, '/ops-center': 63,
  '/ops-extras': 64, '/open': 65, '/gov': 66,
  '/workorders': 70, '/alerts': 71, '/complaints': 72, '/visits': 73,
  '/messages': 74
}

export function useMenu() {
  const auth = useAuthStore()

  const menus = computed(() =>
    menuRoutes.filter((m) => !m.meta?.perm || auth.has(m.meta.perm)))

  /** 按一级分组，组内按 MENU_RANK 排序 */
  const groups = computed(() => {
    const out = []
    for (const name of GROUP_ORDER) {
      const items = menus.value
        .filter((m) => (m.meta?.group || '更多') === name)
        .sort((a, b) => (MENU_RANK[a.path] || 999) - (MENU_RANK[b.path] || 999))
      if (items.length) {
        out.push({ name, icon: GROUP_ICON[name] || 'Menu', items })
      }
    }
    return out
  })

  function titleOf(path) {
    return menuRoutes.find((m) => m.path === path)?.meta?.title || '页面'
  }

  function groupOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    return hit?.meta?.group || '仪表盘'
  }

  return { menus, groups, titleOf, groupOf }
}
'''
io.open(os.path.join(LAY, 'useMenu.js'), 'w', encoding='utf-8').write(MENUS)
print('  ✓ layout/useMenu.js（共用分组与排序）')

# ================= ③ 风格1：宽侧栏 =================
CLASSIC = '''<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '210px'" class="aside">
      <div class="brand">{{ collapsed ? '保' : '住房保障运营平台' }}</div>
      <el-menu :default-active="$route.path" :collapse="collapsed"
               :collapse-transition="false" router class="menu">
        <template v-for="g in groups" :key="g.name">
          <el-sub-menu v-if="g.items.length > 1" :index="g.name">
            <template #title>
              <el-icon><component :is="g.icon" /></el-icon>
              <span>{{ g.name }}</span>
            </template>
            <el-menu-item v-for="m in g.items" :key="m.path" :index="m.path">
              <span>{{ m.meta.title }}</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="g.items[0].path">
            <el-icon><component :is="g.icon" /></el-icon>
            <template #title>{{ g.items[0].meta.title }}</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <el-button text @click="collapsed = !collapsed">
          <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        </el-button>
        <el-breadcrumb separator="/" class="crumb">
          <el-breadcrumb-item>{{ groupOf($route.path) }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ titleOf($route.path) }}</el-breadcrumb-item>
        </el-breadcrumb>
        <div class="spacer" />
        <el-tag size="small" type="info">{{ auth.displayName || '管理员' }}</el-tag>
        <StyleSwitch />
        <el-button text @click="logout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { useMenu } from './useMenu'
import StyleSwitch from './StyleSwitch.vue'

const router = useRouter()
const auth = useAuthStore()
const { groups, titleOf, groupOf } = useMenu()
const collapsed = ref(false)

async function logout() {
  await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100%; }
.aside {
  background: #fff;
  border-right: 1px solid #f0f0f0;
  display: flex; flex-direction: column; height: 100%; overflow: hidden;
  transition: width 0.2s;
}
.brand {
  height: 56px; line-height: 56px; padding: 0 16px;
  color: #1890ff; font-weight: 600; font-size: 15px;
  border-bottom: 1px solid #f0f0f0; flex: 0 0 56px;
  white-space: nowrap; overflow: hidden;
}
.menu {
  border-right: none; flex: 1 1 auto; min-height: 0;
  overflow-y: auto; padding: 4px 0;
}
.menu :deep(.el-menu-item),
.menu :deep(.el-sub-menu__title) {
  height: 40px; line-height: 40px; margin: 2px 8px; border-radius: 6px;
  font-size: 14px;
}
.menu :deep(.el-menu-item.is-active) {
  background: #e6f7ff !important; color: #1890ff !important; font-weight: 500;
}
.header {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border-bottom: 1px solid #f0f0f0;
  height: 56px; padding: 0 16px;
}
.crumb { font-size: 13px; }
.header .spacer { flex: 1; }
.main { background: #f0f2f5; padding: 16px; overflow-y: auto; }
</style>
'''
io.open(os.path.join(LAY, 'LayoutClassic.vue'), 'w', encoding='utf-8').write(CLASSIC)
print('  ✓ LayoutClassic.vue（风格1：宽侧栏分组）')

# ================= ④ 风格2：图标窄栏（沿用当前实现） =================
RAIL = '''<template>
  <el-container class="layout">
    <div class="rail">
      <div class="rail-logo">保</div>
      <div v-for="g in groups" :key="g.name"
           :class="['rail-item', { active: activeGroup === g.name }]"
           @click="pickGroup(g.name)">
        <el-icon :size="20"><component :is="g.icon" /></el-icon>
        <span>{{ g.name }}</span>
      </div>
      <div class="rail-bottom">
        <el-tooltip content="全屏大屏" placement="right">
          <div class="rail-item" @click="openScreen">
            <el-icon :size="18"><Monitor /></el-icon>
          </div>
        </el-tooltip>
      </div>
    </div>

    <div class="panel">
      <div class="panel-title">{{ activeGroup }}</div>
      <el-menu :default-active="$route.path" router class="panel-menu">
        <el-menu-item v-for="m in activeItems" :key="m.path" :index="m.path">
          <span>{{ m.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </div>

    <el-container class="right">
      <el-header class="header">
        <span class="greet">Hi {{ auth.displayName || '管理员' }}，你好~</span>
        <el-breadcrumb separator="/" class="crumb">
          <el-breadcrumb-item>{{ activeGroup }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ titleOf($route.path) }}</el-breadcrumb-item>
        </el-breadcrumb>
        <div class="spacer" />
        <el-tag size="small" type="info">租户 {{ auth.user?.tenantId || '—' }}</el-tag>
        <StyleSwitch />
        <el-button text @click="logout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { useMenu } from './useMenu'
import StyleSwitch from './StyleSwitch.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { groups, titleOf } = useMenu()

const activeGroup = ref('仪表盘')
const activeItems = computed(() =>
  groups.value.find((g) => g.name === activeGroup.value)?.items || [])

function pickGroup(name) {
  activeGroup.value = name
  const g = groups.value.find((x) => x.name === name)
  if (g && !g.items.some((m) => m.path === route.path)) {
    router.push(g.items[0].path)
  }
}

watch(() => route.path, () => {
  const hit = groups.value.find((g) => g.items.some((m) => m.path === route.path))
  if (hit) activeGroup.value = hit.name
}, { immediate: true })

function openScreen() {
  window.open('./view-screen.html', 'bp-screen', 'width=1600,height=900')
}

async function logout() {
  await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100%; }
.rail {
  width: 76px; flex: 0 0 76px; background: #fff;
  border-right: 1px solid #f0f0f0;
  display: flex; flex-direction: column; align-items: center;
  padding: 8px 0; gap: 2px;
}
.rail-logo {
  width: 36px; height: 36px; border-radius: 8px; background: #1890ff;
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-weight: 600; margin-bottom: 10px;
}
.rail-item {
  width: 64px; padding: 8px 0 6px; border-radius: 8px;
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  cursor: pointer; color: rgba(0, 0, 0, 0.65); font-size: 12px;
  transition: background 0.15s, color 0.15s;
}
.rail-item:hover { background: #f5f5f5; }
.rail-item.active { background: #e6f7ff; color: #1890ff; }
.rail-bottom { margin-top: auto; }

.panel {
  width: 168px; flex: 0 0 168px; background: #fff;
  border-right: 1px solid #f0f0f0; padding: 8px 0; overflow: hidden;
}
.panel-title { padding: 6px 16px 10px; font-size: 13px; color: rgba(0, 0, 0, 0.45); }
.panel-menu { border-right: none; }
.panel-menu :deep(.el-menu-item) {
  height: 38px; line-height: 38px; font-size: 14px;
  margin: 0 8px; border-radius: 6px;
}
.panel-menu :deep(.el-menu-item.is-active) {
  background: #e6f7ff; color: #1890ff; font-weight: 500;
}

.right { min-width: 0; }
.header {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border-bottom: 1px solid #f0f0f0;
  height: 56px; padding: 0 16px;
}
.greet { font-size: 15px; color: rgba(0, 0, 0, 0.85); font-weight: 500; }
.crumb { font-size: 13px; }
.header .spacer { flex: 1; }
.main { background: #f0f2f5; padding: 16px; overflow-y: auto; }
</style>
'''
io.open(os.path.join(LAY, 'LayoutRail.vue'), 'w', encoding='utf-8').write(RAIL)
print('  ✓ LayoutRail.vue（风格2：图标窄栏）')

# ================= ⑤ 切换控件 =================
SWITCH = '''<template>
  <el-tooltip :content="`当前：${uiState.style === 'rail' ? '风格2 · 图标窄栏' : '风格1 · 宽侧栏'}（点击切换）`">
    <el-segmented v-model="model" :options="options" size="small"
                  style="margin-right:8px" />
  </el-tooltip>
</template>

<script setup>
import { computed } from 'vue'
import { uiState, setStyle } from './uiState'

const options = [
  { label: '风格1', value: 'classic' },
  { label: '风格2', value: 'rail' }
]

const model = computed({
  get: () => uiState.style,
  set: (v) => setStyle(v)
})
</script>
'''
io.open(os.path.join(LAY, 'StyleSwitch.vue'), 'w', encoding='utf-8').write(SWITCH)
print('  ✓ StyleSwitch.vue（顶部切换控件）')

# ================= ⑥ 入口 Layout：二选一 =================
ENTRY = '''<template>
  <component :is="shell" />
</template>

<script setup>
import { computed } from 'vue'
import { uiState } from './uiState'
import LayoutClassic from './LayoutClassic.vue'
import LayoutRail from './LayoutRail.vue'

/** 两种风格共用同一路由树，切换只换外壳，页面内容完全一致 */
const shell = computed(() =>
  uiState.style === 'classic' ? LayoutClassic : LayoutRail)
</script>
'''
io.open(os.path.join(LAY, 'Layout.vue'), 'w', encoding='utf-8').write(ENTRY)
print('  ✓ Layout.vue（按设置切换外壳）')
