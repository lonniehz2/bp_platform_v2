import { computed } from 'vue'
import { menuRoutes } from '@/router'
import { useAuthStore } from '@/store/auth'

/** 一级分组顺序（两种风格共用） */
export const GROUP_ORDER = [
  '仪表盘', '会员', '线索', '房源', '合同', '财务', '管理后台', '更多'
]

export const GROUP_ICON = {
  仪表盘: 'Odometer',
  会员: 'User',
  线索: 'Tickets',
  房源: 'OfficeBuilding',
  合同: 'Document',
  财务: 'Money',
  管理后台: 'Setting',
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
  '运营总览', '资格准入', '配租与合同', '账务收费',
  '退出与监督', '资产与设备', '服务与协同', '组织与系统'
]

export const CLASSIC_ICON = {
  运营总览: 'DataBoard',
  资格准入: 'Tickets',
  配租与合同: 'Document',
  账务收费: 'Money',
  退出与监督: 'SwitchButton',
  资产与设备: 'OfficeBuilding',
  服务与协同: 'Service',
  组织与系统: 'Setting'
}

/** 路径 → 风格1 分组 */
const CLASSIC_GROUP = {
  '/dashboard': '运营总览', '/reports': '运营总览', '/todos': '运营总览',

  '/persons': '资格准入', '/applications': '资格准入',
  '/waitlist': '资格准入', '/publicities': '资格准入',
  '/annual-reviews': '资格准入',

  '/allocations': '配租与合同', '/contracts': '配租与合同',
  '/contract-changes': '配租与合同', '/exchanges': '配租与合同',

  '/fee-items': '账务收费', '/bills': '账务收费', '/deposits': '账务收费',
  '/arrears': '账务收费', '/subsidies': '账务收费', '/cashflow': '账务收费',

  '/terminations': '退出与监督', '/credits': '退出与监督',
  '/appeals': '退出与监督',

  '/houses': '资产与设备', '/spaces': '资产与设备',
  '/house-calendar': '资产与设备', '/short-rent': '资产与设备',
  '/devices': '资产与设备', '/access': '资产与设备',
  '/keyring': '资产与设备', '/grants': '资产与设备',

  '/workorders': '服务与协同', '/alerts': '服务与协同',
  '/complaints': '服务与协同', '/visits': '服务与协同',
  '/messages': '服务与协同',

  '/orgs': '组织与系统', '/rbac': '组织与系统', '/sys': '组织与系统',
  '/ops-center': '组织与系统', '/ops-extras': '组织与系统',
  '/open': '组织与系统', '/gov': '组织与系统'
}

export function useMenu() {
  const auth = useAuthStore()

  const menus = computed(() =>
    menuRoutes.filter((m) => !m.meta?.perm || auth.has(m.meta.perm)))

  /** 按一级分组，组内按 MENU_RANK 排序 */
  const groups = computed(() => {
    const out = []
    for (const name of GROUP_ORDER) {
      const items = menus.value
        .filter((m) => (m.meta?.group || '更多') === name)
        .sort((a, b) => (MENU_RANK[a.path] || 999) - (MENU_RANK[b.path] || 999))
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
        .filter((m) => CLASSIC_GROUP[m.path] === name)
        .sort((a, b) => (MENU_RANK[a.path] || 999) - (MENU_RANK[b.path] || 999))
      if (items.length) {
        out.push({ name, icon: CLASSIC_ICON[name] || 'Menu', items })
      }
    }
    return out
  })

  function titleOf(path) {
    return menuRoutes.find((m) => m.path === path)?.meta?.title || '页面'
  }

  function groupOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    return hit?.meta?.group || '仪表盘'
  }

  return { menus, groups, classicGroups, titleOf, groupOf }
}
