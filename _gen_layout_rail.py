# -*- coding: utf-8 -*-
"""按参考系统重做布局：图标窄栏 + 二级菜单面板 + 顶部问候栏"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 路由分组改为参考系统的 8 个一级 ----------
R = os.path.join(FE, 'router', 'index.js')
s = io.open(R, encoding='utf-8').read()

GROUP = {
    'dashboard': '仪表盘', 'screen': '仪表盘',
    'persons': '会员',
    'applications': '线索', 'waitlist': '线索', 'publicities': '线索',
    'annual-reviews': '线索',
    'houses': '房源', 'spaces': '房源', 'house-calendar': '房源',
    'short-rent': '房源', 'devices': '房源', 'access': '房源',
    'keyring': '房源', 'grants': '房源',
    'contracts': '合同', 'contract-changes': '合同', 'exchanges': '合同',
    'terminations': '合同', 'allocations': '合同',
    'bills': '财务', 'deposits': '财务', 'arrears': '财务', 'subsidies': '财务',
    'cashflow': '财务', 'fee-items': '财务', 'reports': '财务',
    'orgs': '管理后台', 'rbac': '管理后台', 'sys': '管理后台',
    'open': '管理后台', 'gov': '管理后台', 'ops-center': '管理后台',
    'ops-extras': '管理后台',
    'workorders': '更多', 'alerts': '更多', 'complaints': '更多',
    'visits': '更多', 'messages': '更多',
}

n = 0
for path, grp in GROUP.items():
    pat = re.compile(r"(path:\s*'/%s',[\s\S]{0,400}?meta:\s*\{[^}]*?)group:\s*'[^']*'"
                     % re.escape(path))
    m = pat.search(s)
    if m:
        old = re.search(r"group:\s*'([^']*)'", m.group(0)).group(1)
        if old != grp:
            s = s[:m.start()] + m.group(0).replace("group: '%s'" % old,
                                                   "group: '%s'" % grp) + s[m.end():]
            n += 1
io.open(R, 'w', encoding='utf-8').write(s)
print('  ✓ 路由分组改为 8 个一级导航（调整 %d 条）' % n)

# ---------- 2) Layout 重做：图标窄栏 + 二级面板 ----------
LAYOUT = '''<template>
  <el-container class="layout">
    <!-- 图标窄栏：与参考系统一致，图标 + 两字标签 -->
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
        <el-tooltip content="退出登录" placement="right">
          <div class="rail-item" @click="logout">
            <el-icon :size="18"><SwitchButton /></el-icon>
          </div>
        </el-tooltip>
      </div>
    </div>

    <!-- 二级菜单面板 -->
    <div class="panel" :class="{ hidden: !activeGroup }">
      <div class="panel-title">{{ activeGroup }}</div>
      <el-menu :default-active="$route.path" router class="panel-menu">
        <el-menu-item v-for="m in activeItems" :key="m.path" :index="m.path">
          <span>{{ m.meta.title }}</span>
        </el-menu-item>
      </el-menu>
    </div>

    <el-container class="right">
      <!-- 顶部：问候 + 面包屑 + 用户 -->
      <el-header class="header">
        <span class="greet">Hi {{ auth.displayName || '管理员' }}，你好~</span>
        <el-breadcrumb class="crumb" separator="/">
          <el-breadcrumb-item>{{ activeGroup }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ titleOf($route.path) }}</el-breadcrumb-item>
        </el-breadcrumb>
        <div class="spacer" />
        <el-tag size="small" type="info">租户 {{ auth.user?.tenantId || '—' }}</el-tag>
        <el-button text @click="logout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <component :is="Component" />
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { menuRoutes } from '@/router'
import { useAuthStore } from '@/store/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

/** 一级导航（顺序与参考系统一致） */
const groups = [
  { name: '仪表盘', icon: 'Odometer' },
  { name: '会员', icon: 'User' },
  { name: '线索', icon: 'Tickets' },
  { name: '房源', icon: 'OfficeBuilding' },
  { name: '合同', icon: 'Document' },
  { name: '财务', icon: 'Money' },
  { name: '管理后台', icon: 'Setting' },
  { name: '更多', icon: 'Grid' }
]

const activeGroup = ref('仪表盘')

const menus = computed(() =>
  menuRoutes.filter((m) => !m.meta?.perm || auth.has(m.meta.perm)))

const activeItems = computed(() =>
  menus.value.filter((m) => (m.meta?.group || '更多') === activeGroup.value))

function pickGroup(name) {
  activeGroup.value = name
  const first = menus.value.find((m) => (m.meta?.group || '更多') === name)
  if (first && !activeItems.value.some((m) => m.path === route.path)) {
    router.push(first.path)
  }
}

function titleOf(path) {
  return menuRoutes.find((m) => m.path === path)?.meta?.title || '页面'
}

/** 路由变化时同步高亮所在分组 */
watch(() => route.path, (p) => {
  const hit = menuRoutes.find((m) => m.path === p)
  if (hit?.meta?.group) activeGroup.value = hit.meta.group
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

/* ---------- 图标窄栏 ---------- */
.rail {
  width: 76px;
  flex: 0 0 76px;
  background: #fff;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  gap: 2px;
}
.rail-logo {
  width: 36px; height: 36px; border-radius: 8px;
  background: #1890ff; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 600; margin-bottom: 10px;
}
.rail-item {
  width: 64px;
  padding: 8px 0 6px;
  border-radius: 8px;
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.65);
  font-size: 12px;
  transition: background 0.15s, color 0.15s;
}
.rail-item:hover { background: #f5f5f5; }
.rail-item.active { background: #e6f7ff; color: #1890ff; }
.rail-bottom { margin-top: auto; display: flex; flex-direction: column; gap: 2px; }

/* ---------- 二级菜单面板 ---------- */
.panel {
  width: 168px;
  flex: 0 0 168px;
  background: #fff;
  border-right: 1px solid #f0f0f0;
  padding: 8px 0;
  transition: width 0.2s, flex-basis 0.2s;
  overflow: hidden;
}
.panel.hidden { width: 0; flex-basis: 0; border-right: none; }
.panel-title {
  padding: 6px 16px 10px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
}
.panel-menu { border-right: none; }
.panel-menu :deep(.el-menu-item) {
  height: 38px; line-height: 38px; font-size: 14px;
  margin: 0 8px; border-radius: 6px;
}
.panel-menu :deep(.el-menu-item.is-active) {
  background: #e6f7ff; color: #1890ff; font-weight: 500;
}

/* ---------- 顶部 ---------- */
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
io.open(os.path.join(FE, 'layout', 'Layout.vue'), 'w', encoding='utf-8').write(LAYOUT)
print('  ✓ Layout.vue 重做（图标窄栏 + 二级面板 + 问候栏）')
