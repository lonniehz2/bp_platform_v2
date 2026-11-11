const BASE = process.env.PLATFORM_BASE || 'http://127.0.0.1:8091'
const API = `${BASE}/api/v1`
const login = await fetch(`${API}/auth/login`, {
  method: 'POST', headers: { 'content-type': 'application/json' },
  body: JSON.stringify({ tenantCode: '350600', username: process.env.PLATFORM_USER || 'admin', password: process.env.PLATFORM_PASSWORD || 'admin123' })
}).then(r => r.json())
if (login.code !== 'BP00000') throw new Error(`login failed: ${login.messageKey || login.code}`)
const headers = { Authorization: `Bearer ${login.data.token}` }
const scenes = { GUARANTEE: 'GUARANTEE_', ASSET: 'ASSET_', SERVICE: 'SERVICE_' }
let failed = false
for (const [scene, prefix] of Object.entries(scenes)) {
  const tree = await fetch(`${API}/auth/menu-tree?sceneCode=${scene}`, { headers }).then(r => r.json())
  const roles = await fetch(`${API}/platform/roles?sceneCode=${scene}`, { headers }).then(r => r.json())
  if (!Array.isArray(tree.data) || tree.data.length !== 10) { console.error(`[scene-data] ${scene} 菜单分组数异常`); failed = true }
  if (!Array.isArray(roles.data) || roles.data.length < 4) { console.error(`[scene-data] ${scene} 角色模板不足`); failed = true }
  for (const role of roles.data || []) {
    if (!String(role.roleCode).startsWith(prefix)) { console.error(`[scene-data] ${scene} 角色编码不属于场景：${role.roleCode}`); failed = true }
    if (String(role.roleCode).includes('VERIFY')) { console.error(`[scene-data] ${scene} 残留测试角色：${role.roleCode}`); failed = true }
  }
}
if (failed) process.exit(1)
console.log('[scene-data] 通过：三个场景各有 10 个菜单分组和场景专属角色')
