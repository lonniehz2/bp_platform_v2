import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import { i18n } from './i18n'
import { installPageI18n } from './auto-i18n'
import './styles.css'

import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import Projects from './pages/Projects.vue'
import Persons from './pages/Persons.vue'
import Applications from './pages/Applications.vue'
import Contracts from './pages/Contracts.vue'
import Billing from './pages/Billing.vue'
import Deposits from './pages/Deposits.vue'
import Arrears from './pages/Arrears.vue'
import Cashflow from './pages/Cashflow.vue'
import Reports from './pages/Reports.vue'
import FeeItems from './pages/FeeItems.vue'
import Changes from './pages/Changes.vue'
import Audit from './pages/Audit.vue'
import WorkOrders from './pages/WorkOrders.vue'
import Access from './pages/Access.vue'
import Complaints from './pages/Complaints.vue'
import Publicity from './pages/Publicity.vue'
import Alerts from './pages/Alerts.vue'
import Credit from './pages/Credit.vue'
import ShortRent from './pages/ShortRent.vue'
import Qualification from './pages/Qualification.vue'
import MigrationExceptions from './pages/MigrationExceptions.vue'
import Devices from './pages/Devices.vue'
import Meters from './pages/Meters.vue'
import Menus from './pages/Menus.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', component: Login, meta: { title: '登录', public: true } },
    { path: '/', component: Dashboard, meta: { title: '工作台' } },
    { path: '/projects', component: Projects, meta: { title: '项目与资产' } },
    { path: '/persons', component: Persons, meta: { title: '客户与人员' } },
    { path: '/applications', component: Applications, meta: { title: '申请与轮候' } },
    { path: '/contracts', component: Contracts, meta: { title: '合同与租赁' } },
    { path: '/billing', component: Billing, meta: { title: '收费与账务' } },
    { path: '/deposits', component: Deposits, meta: { title: '押金与补贴' } },
    { path: '/arrears', component: Arrears, meta: { title: '欠费清单' } },
    { path: '/cashflow', component: Cashflow, meta: { title: '资金流水' } },
    { path: '/fee-items', component: FeeItems, meta: { title: '计费项目' } },
    { path: '/reports', component: Reports, meta: { title: '运营报表' } },
    { path: '/changes', component: Changes, meta: { title: '合同变更' } },
    { path: '/qualification', component: Qualification, meta: { title: '资格复核' } },
    { path: '/meters', component: Meters, meta: { title: '计量与能耗' } },
    { path: '/devices', component: Devices, meta: { title: '设备与授权' } },
    { path: '/work-orders', component: WorkOrders, meta: { title: '服务与工单' } },
    { path: '/access-records', component: Access, meta: { title: '访客通行' } },
    { path: '/complaints', component: Complaints, meta: { title: '投诉与申诉' } },
    { path: '/publicities', component: Publicity, meta: { title: '公示管理' } },
    { path: '/alerts', component: Alerts, meta: { title: '风险告警' } },
    { path: '/credits', component: Credit, meta: { title: '信用惩戒' } },
    { path: '/short-rent-orders', component: ShortRent, meta: { title: '短租订单' } },
    { path: '/audit', component: Audit, meta: { title: '审批中心' } },
    { path: '/menus', component: Menus, meta: { title: '菜单与角色' } },
    { path: '/migration-exceptions', component: MigrationExceptions, meta: { title: '迁移异常' } }
  ]
})

router.beforeEach((to) => {
  const token = localStorage.getItem('platformToken')
  if (!to.meta.public && !token) return '/login'
  if (to.path === '/login' && token) return '/'
})

createApp(App).use(i18n).use(router).mount('#app')
installPageI18n(i18n.global.locale)
