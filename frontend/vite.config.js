import { defineConfig } from 'vite'
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
      // 首屏分包：把体积大的第三方库拆出来，避免单包 1.2MB
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('echarts') || id.includes('zrender')) return 'echarts'
            if (id.includes('element-plus')) return 'element-plus'
            if (id.includes('@element-plus/icons-vue')) return 'ep-icons'
            return 'vendor'
          }
        }
      },
      input: {
        main: resolve(__dirname, 'index.html'),
        h5: resolve(__dirname, 'h5.html'),
        screen: resolve(__dirname, 'view-screen.html')
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
