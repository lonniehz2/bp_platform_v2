import io
p=r'src\api.js'
s=io.open(p,encoding='utf-8').read()
if 'myPermissions' not in s:
 s=s.replace("  myMenus: (sceneCode = 'GUARANTEE') =>", "  myPermissions: () => fetch(`${AUTH}/permissions`, { headers: { Authorization: `Bearer ${token()}` } }).then(async r => { const j = await r.json().catch(() => ({})); if (!r.ok || j.code !== 'BP00000') throw new Error(j.message || '获取权限失败'); return j.data || [] }),\n  myMenus: (sceneCode = 'GUARANTEE') =>")
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\permissions.js'
s=io.open(p,encoding='utf-8').read()
if 'canAction' not in s:
 s += '''

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
'''
io.open(p,'w',encoding='utf-8',newline='').write(s)
p=r'src\pages\Login.vue'
s=io.open(p,encoding='utf-8').read()
s=s.replace('''    try {
      const menus = await api.myMenus('GUARANTEE')
      localStorage.setItem('platformMenus', JSON.stringify(menus))
    } catch {}''','''    try {
      const menus = await api.myMenus('GUARANTEE')
      localStorage.setItem('platformMenus', JSON.stringify(menus))
    } catch {}
    try {
      const actions = await api.myPermissions()
      localStorage.setItem('platformPermissions', JSON.stringify(actions))
    } catch {}''')
io.open(p,'w',encoding='utf-8',newline='').write(s)
print('frontend permissions')
