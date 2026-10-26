/**
 * 菜单展开状态：按角色给默认展开项，并记住用户的手动选择。
 *
 * 优先级：用户手动选择（localStorage） > 角色默认（依据页面权限推断） > 全收起
 */
const KEY_PREFIX = 'bp.menu.open.'

/** 分组 → 触发条件（任一页面权限即可认为该角色关心这个分组） */
const GROUP_TRIGGERS = [
  ['收费与账务', ['page:bills:view', 'page:arrears:view', 'page:fee-items:view']],
  ['合同与租赁', ['page:contracts:view', 'page:terminations:view', 'page:exchanges:view']],
  ['设备与通行', ['page:devices:view', 'page:keyring:view', 'page:grants:view',
    'page:access:view']],
  ['房源与空间', ['page:houses:view', 'page:spaces:view', 'page:house-calendar:view']],
  ['计量与能耗', ['page:meter-readings:view', 'page:energy:view']],
  ['服务与监督', ['page:workorders:view', 'page:alerts:view', 'page:complaints:view']],
  ['保障与资格', ['page:persons:view', 'page:annual-reviews:view',
    'page:applications:view', 'page:waitlist:view']],
  ['系统与数据', ['page:orgs:view', 'page:rbac:view', 'page:sys:view']]
]

/** 所有角色都默认展开 */
const ALWAYS_OPEN = ['工作台']

/**
 * 依据权限推断角色默认展开的分组。
 *
 * @param {(code: string) => boolean} has 权限判断函数
 */
export function defaultOpenGroups(has) {
  const open = new Set(ALWAYS_OPEN)
  for (const [group, codes] of GROUP_TRIGGERS) {
    if (codes.some((c) => has(c))) {
      open.add(group)
    }
  }
  // 权限过少（如仅租户）时，至少展开合同与账务，避免"只开一个组"
  if (open.size <= 2) {
    open.add('合同与租赁')
    open.add('收费与账务')
  }
  return Array.from(open)
}

function keyOf(userId) {
  return KEY_PREFIX + (userId || 'anon')
}

/** 读取用户上次保存的展开状态；没有则返回 null。 */
export function loadOpenGroups(userId) {
  try {
    const raw = localStorage.getItem(keyOf(userId))
    if (!raw) return null
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : null
  } catch (e) {
    return null
  }
}

/** 保存展开状态。 */
export function saveOpenGroups(userId, groups) {
  try {
    localStorage.setItem(keyOf(userId), JSON.stringify(groups || []))
  } catch (e) { /* 忽略配额等异常 */ }
}
