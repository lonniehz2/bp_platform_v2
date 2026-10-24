<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '210px'" class="aside">
      <div class="brand">{{ collapsed ? '保' : '住房保障运营平台' }}</div>
      <el-menu :default-active="$route.path" :collapse="collapsed"
               :collapse-transition="false" :default-openeds="openedGroups"
               router class="menu" @open="onMenuOpen" @close="onMenuClose">
        <template v-for="g in groups" :key="g.name">
          <el-sub-menu v-if="g.items.length > 1" :index="g.name">
            <template #title>
              <el-icon><component :is="g.icon" /></el-icon>
              <span>{{ g.name }}</span>
            </template>
            <el-menu-item v-for="m in g.items" :key="m.path" :index="m.path">
              <span>{{ m.meta.title }}</span>
              <el-badge v-if="m.path === '/todos' && todo.total > 0" :value="todo.total"
                        :max="99" style="margin-left:8px" />
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
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import { useMenu } from './useMenu'
import { useTodoStore } from '@/store/todo'
import StyleSwitch from './StyleSwitch.vue'
import { defaultOpenGroups, loadOpenGroups, saveOpenGroups } from './menuPrefs'

const router = useRouter()
const auth = useAuthStore()
const todo = useTodoStore()
const { classicGroups: groups, titleOf, groupOf } = useMenu()
const collapsed = ref(false)

/**
 * 菜单展开状态：按角色默认 + 记住用户手动选择。
 *
 * 默认展开依据页面权限推断（见 menuPrefs.js），用户点开/收起后写入 localStorage。
 */
const openedGroups = ref((() => {
  const saved = loadOpenGroups(null)
  const base = defaultOpenGroups((code) => auth.has(code))
  return (saved && saved.length) ? saved : base
})())
const menuRef = ref(null)
const menuKey = ref(0)
const menuReady = ref(false)

function initOpenGroups() {
  const saved = loadOpenGroups(auth.user?.userId)
  openedGroups.value = (saved && saved.length)
    ? saved
    : defaultOpenGroups((code) => auth.has(code))
  // 展开状态确定后再挂载菜单，确保 default-openeds 生效
  menuReady.value = true
  nextTick(() => {
    menuKey.value++
    nextTick(() => applyOpen())
  })
}

function applyOpen() {
  const menu = menuRef.value
  if (!menu) return
  for (const g of openedGroups.value) {
    try { menu.open(g) } catch (e) { /* 分组未渲染 */ }
  }
}

function onMenuOpen(index) {
  if (!openedGroups.value.includes(index)) {
    openedGroups.value = [...openedGroups.value, index]
    saveOpenGroups(auth.user?.userId, openedGroups.value)
  }
}

function onMenuClose(index) {
  openedGroups.value = openedGroups.value.filter((x) => x !== index)
  saveOpenGroups(auth.user?.userId, openedGroups.value)
}

onMounted(initOpenGroups)
watch(() => groups.value.length, (n) => {
  if (n > 0) {
    // 子菜单渲染需要多帧，延迟兜底展开
    setTimeout(() => applyOpen(), 300)
  }
}, { immediate: true })
watch(() => auth.user?.userId, initOpenGroups)
watch(() => (auth.permissions || []).length, (n) => {
  if (n > 0 && !loadOpenGroups(auth.user?.userId)) {
    initOpenGroups()
  }
})

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
