export function getMenus() {
  try {
    const value = JSON.parse(localStorage.getItem('platformMenus') || '[]')
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

export function can(menu) {
  const menus = getMenus()
  // 未加载时先放开，后端仍会做 403 校验
  return menus.length === 0 || menus.includes(menu)
}

export function setMenus(menus) {
  localStorage.setItem('platformMenus', JSON.stringify(menus || []))
}


const ACTION_KEY = 'platformPermissions'

export function getActions() {
  try {
    const value = JSON.parse(localStorage.getItem(ACTION_KEY) || '[]')
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

export function canAction(action, fallbackMenu) {
  const actions = getActions()
  if (!actions.length) return fallbackMenu ? can(fallbackMenu) : true
  if (actions.includes('*') || actions.includes(action)) return true
  return actions.some(p => p.endsWith(':*') && action.startsWith(p.slice(0, -1)))
}
