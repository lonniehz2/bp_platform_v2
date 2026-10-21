# -*- coding: utf-8 -*-
"""生成 H5 租客端：多页入口 + 核心骨架 + 底部导航"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

# ---------- 多页入口配置 ----------
F['vite.config.js'] = '''import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { resolve } from 'node:path'

// 多页构建：
//   index.html → PC 管理台（Vue SPA）
//   h5.html    → 租客端 H5（移动优先）
// 构建产物直接输出到后端 static 目录，私有化部署仍是「一个 jar」
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    outDir: '../backend/src/main/resources/static',
    emptyOutDir: false,
    chunkSizeWarningLimit: 1600,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        h5: resolve(__dirname, 'h5.html')
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://192.168.31.11:8080', changeOrigin: true }
    }
  }
})
'''

F['h5.html'] = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport"
        content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <meta name="theme-color" content="#1f6feb" />
  <title>住房保障 · 租客端</title>
</head>
<body>
  <div id="h5"></div>
  <script type="module" src="/src/h5/main.js"></script>
</body>
</html>
'''

F['src/h5/main.js'] = '''import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './h5.css'

const app = createApp(App)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#h5')
'''

F['src/h5/App.vue'] = '''<template>
  <div class="h5-root">
    <router-view />
    <nav v-if="showTab" class="tabbar">
      <div v-for="t in tabs" :key="t.path" :class="['tab', { active: isActive(t.path) }]"
           @click="$router.push(t.path)">
        <el-icon :size="20"><component :is="t.icon" /></el-icon>
        <span>{{ t.label }}</span>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const tabs = [
  { path: '/h5/home', label: '首页', icon: 'HomeFilled' },
  { path: '/h5/bills', label: '账单', icon: 'Money' },
  { path: '/h5/applications', label: '申请', icon: 'Document' },
  { path: '/h5/profile', label: '我的', icon: 'User' }
]
const showTab = computed(() => !route.meta.hideTab)
function isActive(p) { return route.path.startsWith(p) }
</script>
'''

F['src/h5/h5.css'] = '''* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

html, body, #h5 { height: 100%; margin: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f2f4f7;
  color: #1d2129;
  font-size: 14px;
}

.h5-root { min-height: 100%; padding-bottom: 56px; }

.navbar {
  height: 48px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  background: #1f6feb;
  color: #fff;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 10;
}
.navbar .back { margin-right: 8px; cursor: pointer; }

.card {
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  margin: 10px 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.hero {
  background: linear-gradient(135deg, #1f6feb, #3f8cff);
  color: #fff;
  border-radius: 0 0 18px 18px;
  padding: 18px 16px 22px;
  margin-bottom: -8px;
}
.hero .title { font-size: 18px; font-weight: 600; }
.hero .sub { font-size: 12px; opacity: 0.85; margin-top: 4px; }

.grid4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  text-align: center;
}
.grid4 .item { padding: 10px 0; cursor: pointer; }
.grid4 .item .icon { font-size: 22px; color: #1f6feb; }
.grid4 .item .label { font-size: 12px; margin-top: 6px; color: #4e5969; }

.row { display: flex; align-items: center; gap: 8px; }
.row .spacer { flex: 1; }
.muted { color: #86909c; font-size: 12px; }

.amount { font-size: 22px; font-weight: 600; color: #f53f3f; }
.amount.ok { color: #00b42a; }

.list-item {
  padding: 12px 0;
  border-bottom: 1px solid #f2f3f5;
}
.list-item:last-child { border-bottom: none; }

.tabbar {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  height: 56px;
  background: #fff;
  border-top: 1px solid #e5e6eb;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  z-index: 20;
}
.tabbar .tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 11px;
  color: #86909c;
  cursor: pointer;
}
.tabbar .tab.active { color: #1f6feb; }

.empty { text-align: center; padding: 40px 0; color: #86909c; font-size: 13px; }
'''

F['src/h5/router.js'] = '''import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  { path: '/h5/login', component: () => import('./views/H5Login.vue'),
    meta: { public: true, hideTab: true } },
  { path: '/h5/home', component: () => import('./views/H5Home.vue') },
  { path: '/h5/bills', component: () => import('./views/H5Bills.vue') },
  { path: '/h5/applications', component: () => import('./views/H5Applications.vue') },
  { path: '/h5/access', component: () => import('./views/H5Access.vue'),
    meta: { hideTab: true } },
  { path: '/h5/repairs', component: () => import('./views/H5Repairs.vue'),
    meta: { hideTab: true } },
  { path: '/h5/profile', component: () => import('./views/H5Profile.vue') },
  { path: '/h5', redirect: '/h5/home' },
  { path: '/:pathMatch(.*)*', redirect: '/h5/home' }
]

const router = createRouter({ history: createWebHashHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.loggedIn) return { path: '/h5/login' }
  if (!auth.user) {
    try { await auth.loadMe() } catch (e) { auth.logout(); return { path: '/h5/login' } }
  }
  return true
})

export default router
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件（H5 骨架）' % count)
