import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import { i18n } from './i18n'
import './styles.css'

import Login from './pages/Login.vue'
import Dashboard from './pages/Dashboard.vue'
import Workbench from './pages/Workbench.vue'
import Projects from './pages/Projects.vue'
import Persons from './pages/Persons.vue'
import Applications from './pages/Applications.vue'
import Contracts from './pages/Contracts.vue'
import ContractDetail from './pages/ContractDetail.vue'
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
import EntityDetailPage from './pages/EntityDetailPage.vue'

const baseRoutes = [
    { path: '/login', component: Login, meta: { titleKey: 'login.title', public: true } },
    { path: '/', component: Workbench, meta: { titleKey: 'workbench.title' } },
    { path: '/guarantee/workbench', component: Workbench, meta: { titleKey: 'workbench.title' } },
    { path: '/guarantee/cockpit', component: Dashboard, meta: { titleKey: 'cockpit.title' } },
    { path: '/projects', component: Projects, meta: { titleKey: 'proj.title' } },
    { path: '/persons', component: Persons, meta: { titleKey: 'pp.title' } },
    { path: '/applications', component: Applications, meta: { titleKey: 'ap.title' } },
    { path: '/detail/:type/:id', component: EntityDetailPage, meta: { titleKey: 'detail.title' } },
    { path: '/guarantee/detail/:type/:id', component: EntityDetailPage, meta: { titleKey: 'detail.title' } },
    { path: '/contracts/:id', component: ContractDetail, meta: { titleKey: 'ct.detailTitle' } },
    { path: '/contracts', component: Contracts, meta: { titleKey: 'ct.title' } },
    { path: '/guarantee/dashboard', component: Dashboard, meta: { titleKey: 'cockpit.title' } },
    { path: '/guarantee/assets', component: Projects, meta: { titleKey: 'proj.title' } },
    { path: '/guarantee/persons', component: Persons, meta: { titleKey: 'pp.title' } },
    { path: '/guarantee/applications', component: Applications, meta: { titleKey: 'ap.title' } },
    { path: '/guarantee/waitlist', component: Waitlist, meta: { titleKey: 'waitlist.title' } },
    { path: '/guarantee/allocations', component: Allocations, meta: { titleKey: 'allocations.title' } },
    { path: '/guarantee/contracts/:id', component: ContractDetail, meta: { titleKey: 'ct.detailTitle' } },
    { path: '/guarantee/contracts', component: Contracts, meta: { titleKey: 'ct.title' } },
    { path: '/guarantee/billing', component: Billing, meta: { titleKey: 'billing.billsTitle' } },
    { path: '/guarantee/devices', component: Devices, meta: { titleKey: 'dev.title' } },
    { path: '/guarantee/listings', component: Listings, meta: { titleKey: 'listings.title' } },
    { path: '/billing', component: Billing, meta: { titleKey: 'billing.billsTitle' } },
    { path: '/deposits', alias: '/guarantee/deposits', component: Deposits, meta: { titleKey: 'deposits.title' } },
    { path: '/arrears', alias: '/guarantee/arrears', component: Arrears, meta: { titleKey: 'arrears.title' } },
    { path: '/cashflow', alias: '/guarantee/cashflow', component: Cashflow, meta: { titleKey: 'cashflow.title' } },
    { path: '/fee-items', alias: '/guarantee/fee-items', component: FeeItems, meta: { titleKey: 'fee.title' } },
    { path: '/imports', alias: '/guarantee/imports', component: ImportCenter, meta: { titleKey: 'imp.title' } },
    { path: '/reports', alias: '/guarantee/reports', component: Reports, meta: { titleKey: 'reports.title' } },
    { path: '/changes', component: Changes, meta: { titleKey: 'changes.title' } },
    { path: '/qualification', alias: '/guarantee/qualification', component: Qualification, meta: { titleKey: 'qualification.title' } },
    { path: '/meters', component: Meters, meta: { titleKey: 'meters.title' } },
    { path: '/devices', component: Devices, meta: { titleKey: 'dev.title' } },
    { path: '/work-orders', alias: '/guarantee/work-orders', component: WorkOrders, meta: { titleKey: 'workOrders.title' } },
    { path: '/access-records', component: Access, meta: { titleKey: 'access.title' } },
    { path: '/complaints', alias: '/guarantee/complaints', component: Complaints, meta: { titleKey: 'complaints.title' } },
    { path: '/publicities', alias: '/guarantee/publicities', component: Publicity, meta: { titleKey: 'publicity.title' } },
    { path: '/alerts', alias: '/guarantee/alerts', component: Alerts, meta: { titleKey: 'alerts.title' } },
    { path: '/credits', alias: '/guarantee/credits', component: Credit, meta: { titleKey: 'credit.title' } },
    { path: '/short-rent-orders', component: ShortRent, meta: { titleKey: 'shortRent.title' } },
    { path: '/open-apps', component: OpenApps, meta: { titleKey: 'openApps.title' } },
    { path: '/messages', alias: '/guarantee/messages', component: Messages, meta: { titleKey: 'messages.title' } },
    { path: '/gov-report', component: GovReport, meta: { titleKey: 'govReport.title' } },
    { path: '/search', alias: '/guarantee/search', component: Search, meta: { titleKey: 'search.title' } },
    { path: '/help', alias: '/guarantee/help', component: Help, meta: { titleKey: 'help.title' } },
    { path: '/house-calendar', alias: '/guarantee/house-calendar', component: HouseCalendar, meta: { titleKey: 'calendar.title' } },
    { path: '/energy', component: Energy, meta: { titleKey: 'energy.title' } },
    { path: '/users', redirect: '/rbac/user' },
    { path: '/guarantee/users', redirect: '/rbac/user' },
    { path: '/audit', alias: '/guarantee/audit', component: Audit, meta: { titleKey: 'audit.title' } },
    { path: '/menus', redirect: '/rbac/role' },
    { path: '/guarantee/menus', redirect: '/rbac/role' },
    { path: '/migration-exceptions', component: MigrationExceptions, meta: { titleKey: 'migration.title' } },

    { path: '/todos', alias: '/guarantee/todos', component: Todos, meta: { titleKey: 'todos.title' } },
    { path: '/patrol', alias: '/guarantee/patrol', component: Patrol, meta: { titleKey: 'patrol.title' } },
    { path: '/house-access', alias: '/guarantee/house-access', component: HouseAccess, meta: { titleKey: 'houseAccess.title' } },
    { path: '/visits', alias: '/guarantee/visits', component: Complaints, meta: { titleKey: 'complaints.visitTitle', complaintType: 'VISIT' } },
    { path: '/waitlist', component: Waitlist, meta: { titleKey: 'waitlist.title' } },
    { path: '/allocations', component: Allocations, meta: { titleKey: 'allocations.title' } },
    { path: '/annual-reviews', component: Qualification, meta: { titleKey: 'qualification.annual' } },
    { path: '/contract-changes', alias: '/guarantee/contract-changes', component: Changes, meta: { titleKey: 'changes.title' } },
    { path: '/exchanges', alias: '/guarantee/exchanges', component: Changes, meta: { titleKey: 'changes.room', changeType: 'ROOM_CHANGE' } },
    { path: '/terminations', alias: '/guarantee/terminations', component: Changes, meta: { titleKey: 'changes.termination', changeType: 'TERMINATION' } },
    { path: '/houses', alias: '/guarantee/houses', component: Houses, meta: { titleKey: 'houses.title' } },
    { path: '/spaces', alias: '/guarantee/spaces', component: Spaces, meta: { titleKey: 'spaces.title' } },
    { path: '/bills', component: Billing, meta: { titleKey: 'billing.billsTitle' } },
    { path: '/subsidies', alias: '/guarantee/subsidies', component: Subsidies, meta: { titleKey: 'subsidies.title' } },
    { path: '/meter-readings', component: MeterReadings, meta: { titleKey: 'readings.title' } },
    { path: '/device-bind', alias: '/guarantee/device-bind', component: DeviceBinding, meta: { titleKey: 'deviceBinding.title' } },
    { path: '/dev-events', alias: '/guarantee/dev-events', component: DeviceEvents, meta: { titleKey: 'deviceEvents.title' } },
    { path: '/access', alias: '/guarantee/access', component: AccessRecords, meta: { titleKey: 'accessRecords.title' } },
    { path: '/keyring', alias: '/guarantee/keyring', component: Keyring, meta: { titleKey: 'keyring.title' } },
    { path: '/grants', alias: '/guarantee/grants', component: Grants, meta: { titleKey: 'grants.title' } },
    { path: '/appeals', alias: '/guarantee/appeals', component: Complaints, meta: { titleKey: 'complaints.appealTitle', complaintType: 'APPEAL' } },
    { path: '/orgs', alias: '/guarantee/orgs', component: Orgs, meta: { titleKey: 'orgs.title' } },
    { path: '/gov', alias: '/guarantee/gov', component: GovReport, meta: { titleKey: 'govReport.title' } },
    { path: '/rbac/:tab?', alias: '/guarantee/rbac/:tab?', component: Rbac, meta: { titleKey: 'rbac.title' } },
    { path: '/sys', alias: '/guarantee/sys', component: Sys, meta: { titleKey: 'sys.title' } },
    { path: '/translations', component: Translations, meta: { titleKey: 'translations.title' } },
    { path: '/platform-info', component: PlatformInfo, meta: { titleKey: 'platformInfo.title' } },
    { path: '/short-rent', alias: '/guarantee/short-rent', component: ShortRent, meta: { titleKey: 'shortRent.title' } }
  ]
const routes = [...baseRoutes]
for (const scene of ['asset', 'service']) {
  for (const route of baseRoutes.filter(r => r.path.startsWith('/guarantee'))) {
    const { alias, ...rest } = route
    routes.push({
      ...rest,
      path: '/' + scene + route.path.slice('/guarantee'.length),
      meta: { ...(route.meta || {}) }
    })
  }
}
const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to) => {
  const token = localStorage.getItem('platformToken')
  if (!to.meta.public && !token) return '/login'
  if (to.path === '/login' && token) return '/'
})

createApp(App).use(i18n).use(router).mount('#app')
