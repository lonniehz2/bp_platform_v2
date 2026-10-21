import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import ScreenApp from './ScreenApp.vue'
import './screen.css'

const app = createApp(ScreenApp)
app.use(createPinia())
app.use(ElementPlus, { locale: zhCn })
app.mount('#screen')
