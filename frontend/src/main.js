import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { i18n } from './i18n'
import './styles/index.css'
import './styles/theme.css'

import { fmtMoney } from '@/utils/money'

const app = createApp(App)
app.config.globalProperties.$money = fmtMoney

// 图标全量注册（内部管理台，体积可接受）
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(i18n)
app.use(router)
app.use(ElementPlus)
app.mount('#app')
