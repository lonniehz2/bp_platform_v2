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
