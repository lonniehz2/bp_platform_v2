import io
p=r'src\permissions.js'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''export function can(menu) {
  const menus = getMenus()
  // 未加载时先放开，后端仍会做 403 校验
  return menus.length === 0 || menus.includes(menu)
}''','''export function can(menu) {
  const actions = getActions()
  // 只读角色隐藏所有写操作入口，后端仍有 403 兜底
  if (actions.length > 0 && actions.includes('*:view')
      && !actions.includes('*') && !actions.some(a => a.endsWith(':*'))) {
    return false
  }
  const menus = getMenus()
  // 未加载时先放开，后端仍会做 403 校验
  return menus.length === 0 || menus.includes(menu)
}''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('can readonly')
