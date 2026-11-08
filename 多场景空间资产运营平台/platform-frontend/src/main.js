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
import OpenApps from './pages/OpenApps.vue'
import Messages from './pages/Messages.vue'
import GovReport from './pages/GovReport.vue'
import Search from './pages/Search.vue'
import Help from './pages/Help.vue'
import HouseCalendar from './pages/HouseCalendar.vue'
import Energy from './pages/Energy.vue'
import Users from './pages/Users.vue'
import Qualification from './pages/Qualification.vue'
import MigrationExceptions from './pages/MigrationExceptions.vue'
import Devices from './pages/Devices.vue'
import Meters from './pages/Meters.vue'
import Menus from './pages/Menus.vue'
import Waitlist from './pages/Waitlist.vue'
import Allocations from './pages/Allocations.vue'
import Houses from './pages/Houses.vue'
import Spaces from './pages/Spaces.vue'
import Subsidies from './pages/Subsidies.vue'
import MeterReadings from './pages/MeterReadings.vue'
import Todos from './pages/Todos.vue'
import Keyring from './pages/Keyring.vue'
import Grants from './pages/Grants.vue'
import DeviceEvents from './pages/DeviceEvents.vue'
import DeviceBinding from './pages/DeviceBinding.vue'
import AccessRecords from './pages/AccessRecords.vue'
import Orgs from './pages/Orgs.vue'
import PlatformInfo from './pages/PlatformInfo.vue'
import Sys from './pages/Sys.vue'
import Translations from './pages/Translations.vue'

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
    { path: '/open-apps', component: OpenApps, meta: { title: '开放平台' } },
    { path: '/messages', component: Messages, meta: { title: '消息中心' } },
    { path: '/gov-report', component: GovReport, meta: { title: '监管报送' } },
    { path: '/search', component: Search, meta: { title: '统一查询' } },
    { path: '/help', component: Help, meta: { title: '使用帮助' } },
    { path: '/house-calendar', component: HouseCalendar, meta: { title: '日房态' } },
    { path: '/energy', component: Energy, meta: { title: '能耗分析' } },
    { path: '/users', component: Users, meta: { title: '用户管理' } },
    { path: '/audit', component: Audit, meta: { title: '审批中心' } },
    { path: '/menus', component: Menus, meta: { title: '菜单与角色' } },
    { path: '/migration-exceptions', component: MigrationExceptions, meta: { title: '迁移异常' } },

    // 旧系统路径兼容
    { path: '/todos', component: Todos, meta: { title: '我的待办' } },
    { path: '/patrol', component: Alerts, meta: { title: '自动巡查' } },
    { path: '/house-access', component: Devices, meta: { title: '房源权限' } },
    { path: '/visits', component: Complaints, meta: { title: '入户走访', complaintType: 'VISIT' } },
    { path: '/waitlist', component: Waitlist, meta: { title: '轮候管理' } },
    { path: '/allocations', component: Allocations, meta: { title: '配租摇号' } },
    { path: '/annual-reviews', component: Qualification, meta: { title: '年审复核' } },
    { path: '/contract-changes', component: Changes, meta: { title: '合同变更' } },
    { path: '/exchanges', component: Changes, meta: { title: '换房管理', changeType: 'ROOM_CHANGE' } },
    { path: '/terminations', component: Changes, meta: { title: '退租管理', changeType: 'TERMINATION' } },
    { path: '/houses', component: Houses, meta: { title: '房源台账' } },
    { path: '/spaces', component: Spaces, meta: { title: '空间层级' } },
    { path: '/bills', component: Billing, meta: { title: '账单与缴费' } },
    { path: '/subsidies', component: Subsidies, meta: { title: '补贴管理' } },
    { path: '/meter-readings', component: MeterReadings, meta: { title: '抄表管理' } },
    { path: '/device-bind', component: DeviceBinding, meta: { title: '设备绑定' } },
    { path: '/dev-events', component: DeviceEvents, meta: { title: '设备告警' } },
    { path: '/access', component: AccessRecords, meta: { title: '通行记录' } },
    { path: '/keyring', component: Keyring, meta: { title: '钥匙包' } },
    { path: '/grants', component: Grants, meta: { title: '通行授权' } },
    { path: '/appeals', component: Complaints, meta: { title: '申诉管理', complaintType: 'APPEAL' } },
    { path: '/orgs', component: Orgs, meta: { title: '组织机构' } },
    { path: '/gov', component: GovReport, meta: { title: '监管报送' } },
    { path: '/rbac', component: Users, meta: { title: '用户与权限' } },
    { path: '/sys', component: Sys, meta: { title: '系统支撑' } },
    { path: '/translations', component: Translations, meta: { title: '业务数据翻译' } },
    { path: '/platform-info', component: PlatformInfo, meta: { title: '平台信息' } },
    { path: '/short-rent', component: ShortRent, meta: { title: '短租订单' } }
  ]
})

router.beforeEach((to) => {
  const token = localStorage.getItem('platformToken')
  if (!to.meta.public && !token) return '/login'
  if (to.path === '/login' && token) return '/'
})

createApp(App).use(i18n).use(router).mount('#app')
installPageI18n(i18n.global.locale)
