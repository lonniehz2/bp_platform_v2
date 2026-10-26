import { computed, ref } from 'vue'
import { menuRoutes } from '@/router'
import { useAuthStore } from '@/store/auth'
import {
  GROUP_ORDER, GROUP_ICON, GROUP_ALIAS, SUBGROUPS, MENU_RANK,
  MENU_DESC, MENU_BADGE_KEY, basePathOf, HIDDEN_PATHS
} from './menuConfig'

export { GROUP_ORDER, GROUP_ICON, MENU_DESC, SUBGROUPS }

/** 旧分组名 → 现行分组名的兼容映射（路由 meta 与本地缓存可能仍是旧名） */
const GROUP_ALIAS_LOCAL = GROUP_ALIAS

/** 取规范化后的分组名 */
export function groupNameOf(meta) {
  const g = meta?.group || ''
  return GROUP_ALIAS_LOCAL[g] || g || '系统与数据'
}

/** 无权限时仍显示但禁用（避免「菜单消失＝系统坏了」） */
const showDisabled = ref(true)
export function setShowDisabled(v) {
  showDisabled.value = !!v
}

/**
 * 多 tab 页面的子菜单：按路由 name 索引。
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

/** 路由 path → 页面权限码 page:<slug>:view */
export function pagePermCode(path) {
  const p = String(path || '')
  if (!p || p === '/' || p === '/login') return ''
  const slug = p.replace(/^\//, '').split('/:')[0].replace(/\//g, '-')
  return slug ? `page:${slug}:view` : ''
}

export function useMenu() {
  const auth = useAuthStore()

  /** 全量菜单（含无权限项，标记 disabled） */
  const menus = computed(() => {
    const out = []
    for (const m of menuRoutes) {
      const basePath = NAME_BASE[m.name] || m.path.split('/:')[0]
      // 运维/扩展操作台与业务页重复，菜单不显示（路由仍可直接访问）
      if (HIDDEN_PATHS.includes(basePath)) continue

      const code = m.meta?.perm || pagePermCode(m.path)
      const allowed = !code || auth.has(code)
      if (!allowed && !showDisabled.value) continue

      const tabs = TAB_MENU[m.name]
      const desc = MENU_DESC[basePath] || ''

      // 多页签页面：菜单只占一项，落到默认页签，页内再切换
      const path = tabs && tabs.length ? basePath + '/' + tabs[0].tab : basePath
      out.push({
        path,
        name: m.name,
        meta: m.meta,
        desc,
        badgeKey: MENU_BADGE_KEY[basePath] || '',
        disabled: !allowed,
        _parent: tabs && tabs.length ? basePath : undefined
      })
    }
    return out
  })

  /** 按一级分组，组内按 MENU_RANK 排序，并附分区标题 */
  const groups = computed(() => {
    const out = []
    for (const name of GROUP_ORDER) {
      const items = menus.value
        .filter((m) => groupNameOf(m.meta) === name)
        .sort((a, b) => rankOf(a) - rankOf(b))
      if (!items.length) continue

      // 分区：按 SUBGROUPS 分段，未登记的项归入「其他」
      const spec = SUBGROUPS[name]
      let sections = []
      if (spec) {
        const used = new Set()
        for (const seg of spec) {
          const segItems = items.filter((m) => {
            const base = basePathOf(m.path, m._parent)
            if (seg.paths.includes(base)) {
              used.add(m.path)
              return true
            }
            return false
          })
          if (segItems.length) sections.push({ title: seg.title, items: segItems })
        }
        const rest = items.filter((m) => !used.has(m.path))
        if (rest.length) sections.push({ title: '其他', items: rest })
      } else {
        sections = [{ title: '', items }]
      }

      // items 供路由高亮/跳转逻辑使用，sections 供菜单分区渲染
      const flat = sections.flatMap((x) => x.items)
      out.push({ name, icon: GROUP_ICON[name] || 'Menu', title: name, items: flat, sections })
    }
    return out
  })

  /** 风格1 与风格2 统一使用同一信息架构 */
  const classicGroups = groups

  function rankOf(m) {
    const base = MENU_RANK[m._parent || m.path]
    if (base === undefined) return 999
    if (!m._parent) return base
    const tabs = TAB_MENU[m._parent] || []
    const idx = tabs.findIndex((t) => m.path === m._parent + '/' + t.tab)
    return base + (idx < 0 ? 0 : idx / 100)
  }

  /** 按基础路径找父路由（/rbac/user → /rbac/:tab? 那条） */
  function parentRouteOf(path) {
    const base = String(path || '').split('/:')[0].replace(/\/[^/]+$/, '')
    return menuRoutes.find((m) => {
      const b = NAME_BASE[m.name] || m.path.split('/:')[0]
      return b === base
    })
  }

  function titleOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    if (hit) return hit.meta?.title || '页面'
    // 子页签：/rbac/user → 父页面「用户与权限」+「用户管理」
    const parent = parentRouteOf(path)
    if (!parent) return '页面'
    const tab = String(path).split('/').pop()
    const t = (TAB_MENU[parent.name] || []).find((x) => x.tab === tab)
    const parentTitle = parent.meta?.title || '页面'
    return t ? parentTitle + ' · ' + t.title : parentTitle
  }

  function groupOf(path) {
    const hit = menuRoutes.find((m) => m.path === path)
    if (hit) return groupNameOf(hit.meta)
    const parent = parentRouteOf(path)
    return groupNameOf(parent?.meta)
  }

  return { menus, groups, classicGroups, titleOf, groupOf }
}
