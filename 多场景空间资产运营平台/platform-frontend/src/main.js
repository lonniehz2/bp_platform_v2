import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import './styles.css'

import Dashboard from './pages/Dashboard.vue'
import Projects from './pages/Projects.vue'
import Applications from './pages/Applications.vue'
import Contracts from './pages/Contracts.vue'
import Billing from './pages/Billing.vue'
import Deposits from './pages/Deposits.vue'
import Changes from './pages/Changes.vue'
import Audit from './pages/Audit.vue'
import Devices from './pages/Devices.vue'
import Menus from './pages/Menus.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Dashboard, meta: { title: '工作台' } },
    { path: '/projects', component: Projects, meta: { title: '项目与资产' } },
    { path: '/applications', component: Applications, meta: { title: '申请与轮候' } },
    { path: '/contracts', component: Contracts, meta: { title: '合同与租赁' } },
    { path: '/billing', component: Billing, meta: { title: '收费与账务' } },
    { path: '/deposits', component: Deposits, meta: { title: '押金与补贴' } },
    { path: '/changes', component: Changes, meta: { title: '合同变更' } },
    { path: '/devices', component: Devices, meta: { title: '设备与授权' } },
    { path: '/audit', component: Audit, meta: { title: '审批中心' } },
    { path: '/menus', component: Menus, meta: { title: '菜单与角色' } }
  ]
})

createApp(App).use(router).mount('#app')
