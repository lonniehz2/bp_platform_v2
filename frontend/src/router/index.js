import { createRouter, createWebHashHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

/**
 * 路由表。
 *
 * meta.perm 为访问所需权限码；菜单也由此生成（RBAC 驱动）。
 */
export const menuRoutes = [
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '运营驾驶舱', icon: 'DataBoard', group: '工作台' }
  },
  {
    path: '/applications',
    name: 'applications',
    component: () => import('@/views/Applications.vue'),
    meta: { title: '申请受理', icon: 'Document', group: '保障与资格' }
  },
  {
    path: '/allocations',
    name: 'allocations',
    component: () => import('@/views/Allocations.vue'),
    meta: { title: '配租摇号', icon: 'Tickets', group: '保障与资格' }
  },
  {
    path: '/contracts',
    name: 'contracts',
    component: () => import('@/views/Contracts.vue'),
    meta: { title: '合同台账', icon: 'Files', group: '合同与租赁' }
  },
  {
    path: '/meter-readings',
    name: 'MeterReadings',
    component: () => import('@/views/MeterReadings.vue'),
    meta: { title: '抄表管理', icon: 'Odometer', group: '计量与能耗' }
  },
  {
    path: '/energy',
    name: 'EnergyAnalysis',
    component: () => import('@/views/EnergyAnalysis.vue'),
    meta: { title: '能耗分析', icon: 'TrendCharts', group: '计量与能耗' }
  },
  {
    path: '/bills',
    name: 'bills',
    component: () => import('@/views/Bills.vue'),
    meta: { title: '账单与缴费', icon: 'Money', group: '收费与账务' }
  },
  {
    path: '/reports',
    name: 'reports',
    component: () => import('@/views/Reports.vue'),
    meta: { title: '报表导出', icon: 'Download', group: '系统与数据' }
  },
  {
    path: '/devices',
    name: 'devices',
    component: () => import('@/views/Devices.vue'),
    meta: { title: '设备管理', icon: 'Cpu', group: '设备与通行' }
  },
  {
    path: '/device-bind',
    name: 'DeviceBinding',
    component: () => import('@/views/DeviceBinding.vue'),
    meta: { title: '设备绑定', icon: 'Connection', group: '设备与通行' }
  },
  {
    path: '/dev-events',
    name: 'DevEvents',
    component: () => import('@/views/DevEvents.vue'),
    meta: { title: '设备告警', icon: 'Warning', group: '设备与通行' }
  },
  {
    path: '/access',
    name: 'access',
    component: () => import('@/views/AccessRecords.vue'),
    meta: { title: '通行记录', icon: 'Position', group: '设备与通行' }
  },
  {
    path: '/orgs',
    name: 'orgs',
    component: () => import('@/views/Orgs.vue'),
    meta: { title: '组织机构', icon: 'OfficeBuilding', group: '系统与数据' }
  },
  {
    path: '/houses',
    name: 'houses',
    component: () => import('@/views/Houses.vue'),
    meta: { title: '房源台账', icon: 'House', group: '房源与空间' }
  },
  {
    path: '/todos',
    name: 'todos',
    component: () => import('@/views/Todos.vue'),
    meta: { title: '我的待办', icon: 'AlarmClock', group: '工作台' }
  },
  {
    path: '/messages',
    name: 'messages',
    component: () => import('@/views/Messages.vue'),
    meta: { title: '消息中心', icon: 'Bell', group: '工作台' }
  },
  {
    path: '/workorders',
    name: 'workorders',
    component: () => import('@/views/WorkOrders.vue'),
    meta: { title: '工单维保', icon: 'Tools', group: '服务与监督' }
  },
  {
    path: '/alerts',
    name: 'alerts',
    component: () => import('@/views/Alerts.vue'),
    meta: { title: '告警规则', icon: 'Warning', group: '服务与监督' }
  },
  {
    path: '/keyring',
    name: 'keyring',
    component: () => import('@/views/Keyring.vue'),
    meta: { title: '钥匙包', icon: 'Key', group: '设备与通行', perm: 'keyring:manage' }
  },
  {
    path: '/grants',
    name: 'grants',
    component: () => import('@/views/Grants.vue'),
    meta: { title: '通行授权', icon: 'Link', group: '设备与通行', perm: 'grant:manage' }
  },
  {
    path: '/persons/:tab?',
    name: 'persons',
    component: () => import('@/views/Persons.vue'),
    meta: { title: '人员档案', icon: 'UserFilled', group: '保障与资格' }
  },
  {
    path: '/spaces',
    name: 'spaces',
    component: () => import('@/views/Spaces.vue'),
    meta: { title: '空间层级', icon: 'Grid', group: '房源与空间' }
  },
  {
    path: '/terminations',
    name: 'terminations',
    component: () => import('@/views/Terminations.vue'),
    meta: { title: '退租管理', icon: 'CircleClose', group: '合同与租赁' }
  },
  {
    path: '/appeals',
    name: 'appeals',
    component: () => import('@/views/Appeals.vue'),
    meta: { title: '申诉管理', icon: 'ChatLineSquare', group: '服务与监督' }
  },
  {
    path: '/credits',
    name: 'credits',
    component: () => import('@/views/Credits.vue'),
    meta: { title: '信用惩戒', icon: 'WarningFilled', group: '服务与监督', perm: 'credit:manage' }
  },
  {
    path: '/exchanges',
    name: 'exchanges',
    component: () => import('@/views/Exchanges.vue'),
    meta: { title: '换房管理', icon: 'Switch', group: '合同与租赁' }
  },
  {
    path: '/complaints',
    name: 'complaints',
    component: () => import('@/views/Complaints.vue'),
    meta: { title: '投诉管理', icon: 'BellFilled', group: '服务与监督' }
  },
  {
    path: '/visits',
    name: 'visits',
    component: () => import('@/views/Visits.vue'),
    meta: { title: '入户走访', icon: 'Postcard', group: '服务与监督' }
  },
  {
    path: '/short-rent',
    name: 'shortrent',
    component: () => import('@/views/ShortRent.vue'),
    meta: { title: '短租订单', icon: 'Calendar', group: '房源与空间' }
  },
  {
    path: '/house-calendar',
    name: 'housecalendar',
    component: () => import('@/views/HouseCalendar.vue'),
    meta: { title: '日房态', icon: 'Date', group: '房源与空间' }
  },
  {
    path: '/gov',
    name: 'gov',
    component: () => import('@/views/GovReport.vue'),
    meta: { title: '监管报送', icon: 'Promotion', group: '系统与数据', perm: 'gov:report:list' }
  },
  {
    path: '/open',
    name: 'open',
    component: () => import('@/views/OpenApps.vue'),
    meta: { title: '开放平台', icon: 'Connection', group: '系统与数据', perm: 'open:app:list' }
  },
  {
    path: '/rbac/:tab?',
    name: 'rbac',
    component: () => import('@/views/Rbac.vue'),
    meta: { title: '用户与权限', icon: 'Lock', group: '系统与数据', perm: 'sys:rbac:view' }
  },
  {
    path: '/sys/:tab?',
    name: 'sys',
    component: () => import('@/views/SysAdmin.vue'),
    meta: { title: '系统支撑', icon: 'Setting', group: '系统与数据', perm: 'sys:admin:view' }
  },
  {
    path: '/subsidies',
    name: 'subsidies',
    component: () => import('@/views/Subsidies.vue'),
    meta: { title: '补贴管理', icon: 'Coin', group: '收费与账务' }
  },
  {
    path: '/deposits',
    name: 'deposits',
    component: () => import('@/views/Deposits.vue'),
    meta: { title: '押金与退款', icon: 'Wallet', group: '收费与账务' }
  },
  {
    path: '/publicities',
    name: 'publicities',
    component: () => import('@/views/Publicities.vue'),
    meta: { title: '公示管理', icon: 'Notification', group: '保障与资格' }
  },
  {
    path: '/waitlist',
    name: 'waitlist',
    component: () => import('@/views/Waitlist.vue'),
    meta: { title: '轮候管理', icon: 'Sort', group: '保障与资格' }
  },
  {
    path: '/fee-items',
    name: 'feeitems',
    component: () => import('@/views/FeeItems.vue'),
    meta: { title: '计费项目', icon: 'PriceTag', group: '收费与账务' }
  },
  {
    path: '/arrears',
    name: 'arrears',
    component: () => import('@/views/Arrears.vue'),
    meta: { title: '催缴管理', icon: 'Bell', group: '收费与账务' }
  },
  {
    path: '/cashflow',
    name: 'cashflow',
    component: () => import('@/views/Cashflow.vue'),
    meta: { title: '资金流水', icon: 'TrendCharts', group: '收费与账务' }
  },
  {
    path: '/contract-changes',
    name: 'contractchanges',
    component: () => import('@/views/ContractChanges.vue'),
    meta: { title: '合同变更', icon: 'EditPen', group: '合同与租赁' }
  },
  {
    path: '/annual-reviews',
    name: 'annualreviews',
    component: () => import('@/views/AnnualReviews.vue'),
    meta: { title: '年审复核', icon: 'Checked', group: '保障与资格' }
  },
  {
    path: '/ops-center/:tab?',
    name: 'opscenter',
    component: () => import('@/views/OpsCenter.vue'),
    meta: { title: '运维操作台', icon: 'Tools', group: '系统与数据', perm: 'sys:ops:view' }
  },
  {
    path: '/help',
    name: 'help',
    component: () => import('@/views/Help.vue'),
    meta: { title: '使用帮助', icon: 'QuestionFilled', group: '系统与数据' }
  }
]

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('@/layout/Layout.vue'),
    redirect: '/dashboard',
    children: menuRoutes
  },
  // 独立全屏大屏（第三入口 screen.html，不走 Layout）
  {
    path: '/screen',
    component: () => import('@/views/ScreenPage.vue'),
    // 大屏展示业务数据，必须登录（原 meta.public 属安全隐患，已移除）
    meta: { group: '仪表盘' }
  },
  {
    // 可选 tab 参数：/ops-extras/rule 直达「告警规则」，/ops-extras 落到默认 tab
    path: '/ops-extras/:tab?',
    name: 'opsextras',
    component: () => import('@/views/OpsExtras.vue'),
    meta: { title: '扩展操作台', icon: 'SetUp', group: '系统与数据' }
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 全局守卫：未登录跳登录页；登录后确保已加载权限
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.loggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (!auth.user) {
    try {
      await auth.loadMe()
    } catch (e) {
      auth.logout()
      return { path: '/login' }
    }
  }
  // 无驾驶舱权限的账号（如租户、财务岗）登录后不要停在无权页面
  if (to.path === '/dashboard' && !auth.has('page:dashboard:view')) {
    const first = firstAllowedPath(auth)
    if (first && first !== '/dashboard') return { path: first }
  }
  return true
})

/** 找到该账号第一个有权限的页面（用于登录后落点） */
function firstAllowedPath(auth) {
  for (const m of menuRoutes) {
    const code = m.meta?.perm || pagePermCodeOf(m.path)
    if (code && !auth.has(code)) continue
    // 有子页签的页面落到默认 tab
    return (NAME_BASE_OF[m.name] || m.path.split('/:')[0]) || '/dashboard'
  }
  return '/dashboard'
}

const NAME_BASE_OF = {
  persons: '/persons/person',
  rbac: '/rbac/user',
  sys: '/sys/audit',
  opscenter: '/ops-center/person',
  opsextras: '/ops-extras/msg'
}

function pagePermCodeOf(path) {
  const p = String(path || '')
  if (!p || p === '/' || p === '/login') return ''
  const slug = p.replace(/^\//, '').split('/:')[0].replace(/\//g, '-')
  return slug ? `page:${slug}:view` : ''
}

export default router
