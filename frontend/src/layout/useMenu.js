import { computed } from 'vue'
import { menuRoutes } from '@/router'
import { useAuthStore } from '@/store/auth'

/** 一级分组顺序（两种风格共用） */
export const GROUP_ORDER = [
  '运营总览', '保障对象', '资格准入', '合同管理', '账务收费',
  '授权与交房', '服务与监督', '资产台账', '系统与集成'
]

export const GROUP_ICON = {
  仪表盘: 'Odometer',
  会员: 'User',
  线索: 'Tickets',
  房源: 'OfficeBuilding',
  合同: 'Document',
  财务: 'Money',
  合同管理: 'Document',
  授权与交房: 'Key',
  服务与监督: 'Service',
  资产台账: 'OfficeBuilding',
  系统与集成: 'Setting',
  更多: 'Grid'
}

/** 组内业务顺序 */
const MENU_RANK = {
  '/dashboard': 1,
  '/todos': 2,
  '/persons': 10,
  '/applications': 20, '/waitlist': 21, '/publicities': 22, '/annual-reviews': 23,
  '/houses': 30, '/spaces': 31, '/house-calendar': 32, '/short-rent': 33,
  '/devices': 34, '/access': 35, '/keyring': 36, '/grants': 37,
  '/contracts': 40, '/contract-changes': 41, '/exchanges': 42,
  '/terminations': 43, '/allocations': 44,
  '/fee-items': 50, '/bills': 51, '/deposits': 52, '/arrears': 53,
  '/subsidies': 54, '/cashflow': 55, '/reports': 56,
  '/orgs': 60, '/rbac': 61, '/sys': 62, '/ops-center': 63,
  '/ops-extras': 64, '/open': 65, '/gov': 66,
  '/workorders': 70, '/alerts': 71, '/complaints': 72, '/visits': 73,
  '/messages': 74
}


/**
 * 风格1（宽侧栏）专用分组：按**保障房业务流**划分。
 *
 * 与 meta.group（风格2，参照参考系统的 仪表盘/会员/线索/房源/合同/财务/管理后台/更多）
 * 完全独立，两套并存以便对比两种信息架构。
 */
export const CLASSIC_ORDER = [
  '运营总览', '保障对象', '资格准入', '合同管理', '账务收费',
  '授权与交房', '服务与监督', '资产台账', '系统与集成'
]

export const CLASSIC_ICON = {
  运营总览: 'DataBoard',
  保障对象: 'UserFilled',
  资格准入: 'Tickets',
  合同管理: 'Document',
  账务收费: 'Money',
  授权与交房: 'Key',
  服务与监督: 'Service',
  资产台账: 'OfficeBuilding',
  系统与集成: 'Setting'
}

/** 路径 → 风格1 分组 */
const CLASSIC_GROUP = {
  '/dashboard': '运营总览', '/reports': '运营总览', '/todos': '运营总览',

  '/persons': '保障对象', '/annual-reviews': '保障对象',

  '/applications': '资格准入', '/waitlist': '资格准入',
  '/allocations': '资格准入', '/publicities': '资格准入',

  '/contracts': '合同管理', '/contract-changes': '合同管理',
  '/exchanges': '合同管理', '/terminations': '合同管理',

  '/fee-items': '账务收费', '/bills': '账务收费', '/deposits': '账务收费',
  '/arrears': '账务收费', '/subsidies': '账务收费', '/cashflow': '账务收费',

  '/devices': '授权与交房', '/access': '授权与交房',
  '/keyring': '授权与交房', '/grants': '授权与交房',

  '/workorders': '服务与监督', '/complaints': '服务与监督',
  '/appeals': '服务与监督', '/visits': '服务与监督',
  '/credits': '服务与监督', '/alerts': '服务与监督',
  '/messages': '服务与监督',

  '/houses': '资产台账', '/spaces': '资产台账',
  '/house-calendar': '资产台账', '/short-rent': '资产台账',

  '/orgs': '系统与集成', '/rbac': '系统与集成', '/sys': '系统与集成',
  '/ops-center': '系统与集成', '/ops-extras': '系统与集成',
  '/open': '系统与集成', '/gov': '系统与集成'
}

/**
 * 多 tab 页面的子菜单：**按路由 name 索引**。
 *
 * 早前按 path 索引（'/ops-extras'）在带参数路由上不稳定——OpsExtras 的 6 个 tab
 * 始终不展开（另 3 个页面正常）。name 由路由定义决定、不受 path 参数影响。
 */
export const TAB_MENU = {
  persons: [
    { tab: 'person', title: '人员档案' },
    { tab: 'profile', title: '保障档案' },
    { tab: 'verify', title: '实名核验' }
  ],
  opsextras: [
    { tab: 'msg', title: '消息待办' },
    { tab: 'rule', title: '告警规则' },
    { tab: 'open', title: '开放平台' },
    { tab: 'rbac', title: '权限管理' },
    { tab: 'grant', title: '授权撤销' },
    { tab: 'calendar', title: '日房态' }
  ],
  rbac: [
    { tab: 'user', title: '用户管理' },
    { tab: 'role', title: '角色管理' },
    { tab: 'perm', title: '权限清单' }
  ],
  sys: [
    { tab: 'audit', title: '审计日志' },
    { tab: 'dict', title: '数据字典' },
    { tab: 'config', title: '系统参数' }
  ],
  opscenter: [
    { tab: 'person', title: '人员状态' },
    { tab: 'house', title: '房源状态' },
    { tab: 'order', title: '工单流程' }
  ]
}

/** 路由 name → 基础路径（拼子菜单 URL 用） */
const NAME_BASE = {
  persons: '/persons',
  opsextras: '/ops-extras',
  rbac: '/rbac',
  sys: '/sys',
  opscenter: '/ops-center'
}

export function useMenu() {
  const auth = useAuthStore()

  /** 有子菜单的页面本身不再单独出现，避免「父项 + 子项」重复 */
  const menus = computed(() => {
    const base = menuRoutes.filter((m) => !m.meta?.perm || auth.has(m.meta.perm))
    const out = []
    for (const m of base) {
      const basePath = NAME_BASE[m.name] || m.path.split('/:')[0]
      const tabs = TAB_MENU[m.name]
      if (!tabs) {
        out.push(basePath === m.path ? m : { ...m, path: basePath })
        continue
      }
      for (const t of tabs) {
        out.push({
          path: basePath + '/' + t.tab,
          name: m.name + '-' + t.tab,
          meta: { ...m.meta, title: t.title },
          // 记下父路径，分组与排序回退到父项
          _parent: basePath
        })
      }
    }
    return out
  })

  /** 按一级分组，组内按 MENU_RANK 排序 */
  const groups = computed(() => {
    const out = []
    for (const name of GROUP_ORDER) {
      const items = menus.value
        .filter((m) => (m.meta?.group || '更多') === name)
        .sort((a, b) => rankOf(a) - rankOf(b))
      if (items.length) {
        out.push({ name, icon: GROUP_ICON[name] || 'Menu', items })
      }
    }
    return out
  })

  /** 风格1：按业务流分组 */
  const classicGroups = computed(() => {
    const out = []
    for (const name of CLASSIC_ORDER) {
      const items = menus.value
        .filter((m) => (CLASSIC_GROUP[m.path] || CLASSIC_GROUP[m._parent]) === name)
        .sort((a, b) => rankOf(a) - rankOf(b))
      if (items.length) {
        out.push({ name, icon: CLASSIC_ICON[name] || 'Menu', items })
      }
    }
    return out
  })

  /** 排序权重：子菜单项排在父项位置后，保持原有顺序 */
  function rankOf(m) {
    const base = MENU_RANK[m._parent || m.path]
    if (base === undefined) return 999
    if (!m._parent) return base
    const tabs = TAB_MENU[m._parent] || []
    const idx = tabs.findIndex((t) => m.path === m._parent + '/' + t.tab)
    return base + (idx < 0 ? 0 : idx / 100)
  }

  function titleOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    if (hit) return hit.meta?.title || '页面'
    // 子菜单路径（/ops-extras/rule）回查 TAB_MENU
    const cut = path.lastIndexOf('/')
    const base = path.slice(0, cut)
    const tab = path.slice(cut + 1)
    const t = (TAB_MENU[base] || []).find((x) => x.tab === tab)
    return t ? t.title : '页面'
  }

  function groupOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    if (hit) return hit.meta?.group || '仪表盘'
    const base = path.slice(0, path.lastIndexOf('/'))
    return menuRoutes.find((m) => m.path === base)?.meta?.group || '仪表盘'
  }

  return { menus, groups, classicGroups, titleOf, groupOf }
}
