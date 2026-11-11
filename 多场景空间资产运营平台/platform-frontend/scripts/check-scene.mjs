import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
const read = p => readFileSync(join(root, p), 'utf8')
let failed = false
const fail = msg => { console.error(`[i18n:scene] ${msg}`); failed = true }

for (const dir of ['src/pages', 'src/components']) {
  for (const name of readdirSync(join(root, dir))) {
    if (!name.endsWith('.vue')) continue
    if (read(`${dir}/${name}`).includes('/guarantee')) fail(`${dir}/${name} 仍包含硬编码 /guarantee 路径`)
    if (read(`${dir}/${name}`).includes('GUARANTEE')) fail(`${dir}/${name} 仍包含 GUARANTEE 字面量`)
  }
}
const main = read('src/main.js')
for (const token of ["for (const scene of ['asset', 'service'])", "path: '/' + scene", 'route.meta']) {
  if (!main.includes(token)) fail(`main.js 缺少场景路由标记：${token}`)
}
const scene = read('src/scene.js')
for (const token of ['GUARANTEE', 'ASSET', 'SERVICE', 'scenePath']) {
  if (!scene.includes(token)) fail(`scene.js 缺少：${token}`)
}
const app = read('src/App.vue')
if (!app.includes('scenePath(')) fail('App.vue 菜单未使用 scenePath')
const api = read('src/api.js')
for (const token of ['myMenus: (sceneCode = currentScene())', 'myMenuTree: (sceneCode = currentScene())', 'reportCompare: () => request(`/reports/projects/compare?sceneCode=${currentScene()}`)', 'reportCockpit: (id) => request(`/reports/projects/${id}/cockpit?sceneCode=${currentScene()}`)']) {
  if (!api.includes(token)) fail(`api.js 场景上下文缺失：${token}`)
}
for (const file of ['src/components/RolePanel.vue', 'src/components/PermissionPanel.vue', 'src/pages/Menus.vue', 'src/pages/Audit.vue']) {
  if (!read(file).includes('currentScene')) fail(`${file} 未使用 currentScene`)
}
if (failed) process.exit(1)
console.log('[i18n:scene] 通过：菜单/角色/报表/详情跳转已统一场景上下文，asset/service 路由已生成')
