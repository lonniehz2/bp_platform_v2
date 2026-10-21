# -*- coding: utf-8 -*-
"""生成前端：路由 + 布局 + 登录页"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

F['src/router/index.js'] = '''import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

/**
 * 路由表。
 *
 * meta.perm 为访问所需权限码；菜单也由此生成（RBAC 驱动）。
 */
export const menuRoutes = [
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '运营驾驶舱', icon: 'DataBoard' }
  },
  {
    path: '/applications',
    name: 'applications',
    component: () => import('@/views/Applications.vue'),
    meta: { title: '申请与审核', icon: 'Document' }
  },
  {
    path: '/allocations',
    name: 'allocations',
    component: () => import('@/views/Allocations.vue'),
    meta: { title: '配租与摇号', icon: 'Tickets' }
  },
  {
    path: '/contracts',
    name: 'contracts',
    component: () => import('@/views/Contracts.vue'),
    meta: { title: '合同管理', icon: 'Files' }
  },
  {
    path: '/bills',
    name: 'bills',
    component: () => import('@/views/Bills.vue'),
    meta: { title: '账单与缴费', icon: 'Money' }
  },
  {
    path: '/reports',
    name: 'reports',
    component: () => import('@/views/Reports.vue'),
    meta: { title: '报表导出', icon: 'Download' }
  },
  {
    path: '/devices',
    name: 'devices',
    component: () => import('@/views/Devices.vue'),
    meta: { title: '设备管理', icon: 'Cpu' }
  },
  {
    path: '/access',
    name: 'access',
    component: () => import('@/views/AccessRecords.vue'),
    meta: { title: '通行记录', icon: 'Position' }
  }
]

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/layout/Layout.vue'),
    redirect: '/dashboard',
    children: menuRoutes
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 全局守卫：未登录跳登录页；登录后确保已加载权限
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.loggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (!auth.user) {
    try {
      await auth.loadMe()
    } catch (e) {
      auth.logout()
      return { path: '/login' }
    }
  }
  return true
})

export default router
'''

F['src/layout/Layout.vue'] = '''<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '208px'" class="aside">
      <div class="brand">
        <span v-if="!collapsed">租赁性保障用房</span>
        <span v-else>BP</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="collapsed"
        :collapse-transition="false"
        background-color="#1f2d3d"
        text-color="#c0c4cc"
        active-text-color="#409eff"
        router
      >
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.meta.icon" /></el-icon>
          <template #title>{{ m.meta.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <el-button text @click="collapsed = !collapsed">
          <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        </el-button>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>{{ $route.meta.title || '' }}</el-breadcrumb-item>
        </el-breadcrumb>
        <div class="spacer" />
        <el-tag v-if="auth.admin" type="danger" size="small">管理员</el-tag>
        <span class="user">{{ auth.displayName }}</span>
        <el-dropdown @command="onCommand">
          <el-button text>
            <el-icon><Setting /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="me">我的权限（{{ auth.permissions.length }}）</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view v-slot="{ Component }">
          <keep-alive :max="6">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { menuRoutes } from '@/router'
import { useAuthStore } from '@/store/auth'

const collapsed = ref(false)
const auth = useAuthStore()
const router = useRouter()

// RBAC 驱动：按 meta.perm 过滤菜单（未声明 perm 的菜单登录即可见）
const menus = computed(() =>
  menuRoutes.filter((m) => !m.meta?.perm || auth.has(m.meta.perm))
)

async function onCommand(cmd) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
    try { await router.push('/login') } catch (e) { /* ignore */ }
    auth.logout()
    ElMessage.success('已退出')
  } else if (cmd === 'me') {
    ElMessageBox.alert(
      (auth.permissions.length ? auth.permissions.join('<br/>') : '（无独立权限码，可能是内置管理员）'),
      `当前用户：${auth.displayName}`,
      { dangerouslyUseHTMLString: true }
    )
  }
}
</script>

<style scoped>
.layout { height: 100%; }
.aside {
  background: #1f2d3d;
  transition: width 0.2s;
  overflow: hidden;
}
.brand {
  height: 56px;
  line-height: 56px;
  text-align: center;
  color: #fff;
  font-weight: 600;
  letter-spacing: 1px;
  border-bottom: 1px solid #2b3a4a;
}
.aside :deep(.el-menu) { border-right: none; }
.header {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  height: 56px;
}
.header .spacer { flex: 1; }
.header .user { font-size: 14px; color: #303133; }
.main { background: #f5f7fa; padding: 16px; }
</style>
'''

F['src/views/Login.vue'] = '''<template>
  <div class="login-wrap">
    <div class="login-box">
      <h2>租赁性保障用房管理平台</h2>
      <p class="sub">Leased Affordable Housing Management Platform</p>

      <el-form :model="form" :rules="rules" ref="formRef" @keyup.enter="onSubmit">
        <el-form-item prop="tenantId">
          <el-input v-model="form.tenantId" placeholder="租户ID" size="large">
            <template #prefix><el-icon><OfficeBuilding /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" size="large">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password
                    placeholder="密码" size="large">
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button type="primary" size="large" style="width:100%"
                   :loading="loading" @click="onSubmit">登 录</el-button>
      </el-form>

      <div class="hint">
        <div class="muted">演示账号（租户 350600）</div>
        <div class="accounts">
          <el-tag v-for="a in accounts" :key="a.u" size="small"
                  style="cursor:pointer;margin:2px"
                  @click="fill(a)">{{ a.label }}</el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ tenantId: '350600', username: 'admin', password: 'admin123' })

const rules = {
  tenantId: [{ required: true, message: '请输入租户ID', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const accounts = [
  { label: '管理员 admin', u: 'admin', p: 'admin123' },
  { label: '受理岗 acceptor', u: 'acceptor', p: 'acc123' },
  { label: '只读 viewer', u: 'viewer', p: 'view123' }
]

function fill(a) {
  form.username = a.u
  form.password = a.p
}

async function onSubmit() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login({ ...form })
    ElMessage.success('登录成功')
    router.replace(route.query.redirect || '/dashboard')
  } catch (e) {
    // 错误提示已在拦截器统一处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f2d3d 0%, #2c5364 100%);
}
.login-box {
  width: 380px;
  background: #fff;
  border-radius: 10px;
  padding: 32px 28px 24px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25);
}
.login-box h2 { margin: 0 0 4px; font-size: 20px; color: #303133; text-align: center; }
.sub { margin: 0 0 22px; text-align: center; color: #909399; font-size: 11px; }
.hint { margin-top: 18px; text-align: center; }
.accounts { margin-top: 6px; }
</style>
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件（路由/布局/登录）' % count)
