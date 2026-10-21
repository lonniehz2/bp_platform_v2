# -*- coding: utf-8 -*-
"""生成前端工程骨架：Vite + Vue3 + Element Plus + Pinia + Router"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

# ==================== 工程配置 ====================
F['package.json'] = '''{
  "name": "bp-platform-web",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.7",
    "echarts": "^5.5.1",
    "element-plus": "^2.8.4",
    "@element-plus/icons-vue": "^2.3.1",
    "pinia": "^2.2.4",
    "vue": "^3.5.11",
    "vue-router": "^4.4.5"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.4",
    "vite": "^5.4.8"
  }
}
'''

F['.npmrc'] = '''registry=https://registry.npmmirror.com
strict-ssl=false
'''

F['vite.config.js'] = '''import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// 构建产物直接输出到后端 static 目录：
// 私有化部署仍然只有「一个 jar」，无需额外静态服务器
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    outDir: '../backend/src/main/resources/static',
    emptyOutDir: false,   // 保留既有 index.html 等文件（由后端兜底页覆盖前请手动确认）
    chunkSizeWarningLimit: 1600
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://192.168.31.11:8080',
        changeOrigin: true
      }
    }
  }
})
'''

F['index.html'] = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>租赁性保障用房管理平台</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
'''

F['src/main.js'] = '''import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './styles/index.css'

const app = createApp(App)

// 图标全量注册（内部管理台，体积可接受）
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
'''

F['src/App.vue'] = '''<template>
  <router-view />
</template>
'''

F['src/styles/index.css'] = '''* { box-sizing: border-box; }

html, body, #app {
  height: 100%;
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
  background: #f5f7fa;
}

.page-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 12px;
}

.toolbar .spacer { flex: 1; }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px 18px;
  border-left: 4px solid #409eff;
}

.stat-card .label { color: #909399; font-size: 13px; }
.stat-card .value { font-size: 26px; font-weight: 600; margin-top: 6px; color: #303133; }
.stat-card.warn { border-left-color: #e6a23c; }
.stat-card.danger { border-left-color: #f56c6c; }
.stat-card.ok { border-left-color: #67c23a; }

.muted { color: #909399; font-size: 12px; }
'''

# ==================== 请求封装 ====================
F['src/api/request.js'] = '''import axios from 'axios'
import { ElMessage } from 'element-plus'

/**
 * 统一请求封装。
 *
 * - 自动带上 Authorization（不透明令牌）与 X-Tenant-Id
 * - 统一解包后端 R<T>：code === 'BP00000' 视为成功
 * - 401 自动回登录页；403 提示无权限
 */
const service = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

const TOKEN_KEY = 'bp_token'
const TENANT_KEY = 'bp_tenant'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(t) {
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}

export function getTenant() {
  return localStorage.getItem(TENANT_KEY) || '350600'
}

export function setTenant(t) {
  localStorage.setItem(TENANT_KEY, t || '350600')
}

service.interceptors.request.use((cfg) => {
  const token = getToken()
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  cfg.headers['X-Tenant-Id'] = getTenant()
  return cfg
})

service.interceptors.response.use(
  (resp) => {
    const body = resp.data
    // 非 R 结构（如文件流）直接返回
    if (!body || typeof body !== 'object' || body.code === undefined) return body
    if (body.code === 'BP00000') return body.data
    ElMessage.error(body.message || `请求失败（${body.code}）`)
    return Promise.reject(body)
  },
  (err) => {
    const status = err.response?.status
    const body = err.response?.data
    if (status === 401) {
      ElMessage.error('登录已失效，请重新登录')
      setToken('')
      setTimeout(() => { window.location.hash = '#/login' }, 300)
    } else if (status === 403) {
      ElMessage.error(body?.message || '无权限访问该功能')
    } else {
      ElMessage.error(body?.message || err.message || '网络异常')
    }
    return Promise.reject(err)
  }
)

export default service
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件（工程骨架）' % count)
