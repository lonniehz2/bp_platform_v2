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
import ImportCenter from './pages/ImportCenter.vue'
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
import Listings from './pages/Listings.vue'
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
import Patrol from './pages/Patrol.vue'
import HouseAccess from './pages/HouseAccess.vue'
import Rbac from './pages/Rbac.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/login', component: Login, meta: { title: '登录', public: true } },
    { path: '/', component: Dashboard, meta: { title: '工作台' } },
    { path: '/projects', component: Projects, meta: { title: '项目与资产' } },
    { path: '/persons', component: Persons, meta: { title: '客户与人员' } },
    { path: '/applications', component: Applications, meta: { title: '申请与轮候' } },
    { path: '/contracts', component: Contracts, meta: { title: '合同与租赁' } },
    { path: '/guarantee/dashboard', component: Dashboard, meta: { title: '运营驾驶舱' } },
    { path: '/guarantee/assets', component: Projects, meta: { title: '项目与资产' } },
    { path: '/guarantee/persons', component: Persons, meta: { title: '客户与人员' } },
    { path: '/guarantee/applications', component: Applications, meta: { title: '申请管理' } },
    { path: '/guarantee/waitlist', component: Waitlist, meta: { title: '轮候配租' } },
    { path: '/guarantee/allocations', component: Allocations, meta: { title: '配租摇号' } },
    { path: '/guarantee/contracts', component: Contracts, meta: { title: '合同与租赁' } },
    { path: '/guarantee/billing', component: Billing, meta: { title: '收费与账务' } },
    { path: '/guarantee/devices', component: Devices, meta: { title: '设备与授权' } },
    { path: '/guarantee/listings', component: Listings, meta: { title: '房源展示' } },
    { path: '/billing', component: Billing, meta: { title: '收费与账务' } },
    { path: '/deposits', alias: '/guarantee/deposits', component: Deposits, meta: { title: '押金与补贴' } },
    { path: '/arrears', alias: '/guarantee/arrears', component: Arrears, meta: { title: '欠费清单' } },
    { path: '/cashflow', alias: '/guarantee/cashflow', component: Cashflow, meta: { title: '资金流水' } },
    { path: '/fee-items', alias: '/guarantee/fee-items', component: FeeItems, meta: { title: '计费项目' } },
    { path: '/imports', alias: '/guarantee/imports', component: ImportCenter, meta: { title: '批量导入' } },
    { path: '/reports', alias: '/guarantee/reports', component: Reports, meta: { title: '运营报表' } },
    { path: '/changes', component: Changes, meta: { title: '合同变更' } },
    { path: '/qualification', alias: '/guarantee/qualification', component: Qualification, meta: { title: '资格复核' } },
    { path: '/meters', component: Meters, meta: { title: '计量与能耗' } },
    { path: '/devices', component: Devices, meta: { title: '设备与授权' } },
    { path: '/work-orders', alias: '/guarantee/work-orders', component: WorkOrders, meta: { title: '服务与工单' } },
    { path: '/access-records', component: Access, meta: { title: '访客通行' } },
    { path: '/complaints', alias: '/guarantee/complaints', component: Complaints, meta: { title: '投诉与申诉' } },
    { path: '/publicities', alias: '/guarantee/publicities', component: Publicity, meta: { title: '公示管理' } },
    { path: '/alerts', alias: '/guarantee/alerts', component: Alerts, meta: { title: '风险告警' } },
    { path: '/credits', alias: '/guarantee/credits', component: Credit, meta: { title: '信用惩戒' } },
    { path: '/short-rent-orders', component: ShortRent, meta: { title: '短租订单' } },
    { path: '/open-apps', component: OpenApps, meta: { title: '开放平台' } },
    { path: '/messages', alias: '/guarantee/messages', component: Messages, meta: { title: '消息中心' } },
    { path: '/gov-report', component: GovReport, meta: { title: '监管报送' } },
    { path: '/search', alias: '/guarantee/search', component: Search, meta: { title: '统一查询' } },
    { path: '/help', alias: '/guarantee/help', component: Help, meta: { title: '使用帮助' } },
    { path: '/house-calendar', alias: '/guarantee/house-calendar', component: HouseCalendar, meta: { title: '日房态' } },
    { path: '/energy', component: Energy, meta: { title: '能耗分析' } },
    { path: '/users', redirect: '/rbac/user' },
    { path: '/guarantee/users', redirect: '/rbac/user' },
    { path: '/audit', alias: '/guarantee/audit', component: Audit, meta: { title: '审批中心' } },
    { path: '/menus', redirect: '/rbac/role' },
    { path: '/guarantee/menus', redirect: '/rbac/role' },
    { path: '/migration-exceptions', component: MigrationExceptions, meta: { title: '迁移异常' } },

    // 旧系统路径兼容
    { path: '/todos', alias: '/guarantee/todos', component: Todos, meta: { title: '我的待办' } },
    { path: '/patrol', alias: '/guarantee/patrol', component: Patrol, meta: { title: '自动巡查' } },
    { path: '/house-access', alias: '/guarantee/house-access', component: HouseAccess, meta: { title: '房源权限' } },
    { path: '/visits', alias: '/guarantee/visits', component: Complaints, meta: { title: '入户走访', complaintType: 'VISIT' } },
    { path: '/waitlist', component: Waitlist, meta: { title: '轮候管理' } },
    { path: '/allocations', component: Allocations, meta: { title: '配租摇号' } },
    { path: '/annual-reviews', component: Qualification, meta: { title: '年审复核' } },
    { path: '/contract-changes', alias: '/guarantee/contract-changes', component: Changes, meta: { title: '合同变更' } },
    { path: '/exchanges', alias: '/guarantee/exchanges', component: Changes, meta: { title: '换房管理', changeType: 'ROOM_CHANGE' } },
    { path: '/terminations', alias: '/guarantee/terminations', component: Changes, meta: { title: '退租管理', changeType: 'TERMINATION' } },
    { path: '/houses', alias: '/guarantee/houses', component: Houses, meta: { title: '房源台账' } },
    { path: '/spaces', alias: '/guarantee/spaces', component: Spaces, meta: { title: '空间层级' } },
    { path: '/bills', component: Billing, meta: { title: '账单与缴费' } },
    { path: '/subsidies', alias: '/guarantee/subsidies', component: Subsidies, meta: { title: '补贴管理' } },
    { path: '/meter-readings', component: MeterReadings, meta: { title: '抄表管理' } },
    { path: '/device-bind', alias: '/guarantee/device-bind', component: DeviceBinding, meta: { title: '设备绑定' } },
    { path: '/dev-events', alias: '/guarantee/dev-events', component: DeviceEvents, meta: { title: '设备告警' } },
    { path: '/access', alias: '/guarantee/access', component: AccessRecords, meta: { title: '通行记录' } },
    { path: '/keyring', alias: '/guarantee/keyring', component: Keyring, meta: { title: '钥匙包' } },
    { path: '/grants', alias: '/guarantee/grants', component: Grants, meta: { title: '通行授权' } },
    { path: '/appeals', alias: '/guarantee/appeals', component: Complaints, meta: { title: '申诉管理', complaintType: 'APPEAL' } },
    { path: '/orgs', alias: '/guarantee/orgs', component: Orgs, meta: { title: '组织机构' } },
    { path: '/gov', alias: '/guarantee/gov', component: GovReport, meta: { title: '监管报送' } },
    { path: '/rbac/:tab?', alias: '/guarantee/rbac/:tab?', component: Rbac, meta: { title: '用户与权限' } },
    { path: '/sys', alias: '/guarantee/sys', component: Sys, meta: { title: '系统支撑' } },
    { path: '/translations', component: Translations, meta: { title: '业务数据翻译' } },
    { path: '/platform-info', component: PlatformInfo, meta: { title: '平台信息' } },
    { path: '/short-rent', alias: '/guarantee/short-rent', component: ShortRent, meta: { title: '短租订单' } }
  ]
})

router.beforeEach((to) => {
  const token = localStorage.getItem('platformToken')
  if (!to.meta.public && !token) return '/login'
  if (to.path === '/login' && token) return '/'
})

createApp(App).use(i18n).use(router).mount('#app')
installPageI18n(i18n.global.locale)
