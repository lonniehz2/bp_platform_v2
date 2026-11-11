import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'

const root = fileURLToPath(new URL('..', import.meta.url))
globalThis.location = { search: '' }
globalThis.localStorage = { getItem: () => null, setItem: () => {} }
const { messages } = await import('../src/i18n.js')
const { navGroups } = await import('../src/navConfig.js')
const design = JSON.parse(readFileSync(join(root, 'scripts/menu-design.json'), 'utf8'))
const get = (obj, path) => path.split('.').reduce((o, k) => o?.[k], obj)
let failed = false
const fail = msg => { console.error(`[menu-labels] ${msg}`); failed = true }
if (navGroups.map(g => g.key).join(',') !== design.map(g => g.key).join(',')) fail('navConfig 分组顺序与设计不一致')
for (const g of design) {
  const zh = get(messages['zh-CN'], `group.${g.key}`)
  if (zh !== g.name) fail(`菜单分组 ${g.key}：设计=${g.name}，实际=${zh}`)
  if (!get(messages['en-US'], `group.${g.key}`)) fail(`菜单分组缺少英文：group.${g.key}`)
  const configured = navGroups.find(x => x.key === g.key)
  if (!configured) { fail(`navConfig 缺少分组：${g.key}`); continue }
  if (configured.items.map(i => i.key).join(',') !== g.items.map(i => i.key).join(',')) fail(`分组 ${g.key} 菜单项与设计不一致`)
  for (const item of g.items) {
    const label = get(messages['zh-CN'], `nav.${item.key}`)
    if (label !== item.name) fail(`菜单项 ${item.key}：设计=${item.name}，实际=${label}`)
    if (!get(messages['en-US'], `nav.${item.key}`)) fail(`菜单项缺少英文：nav.${item.key}`)
  }
}
if (failed) process.exit(1)
console.log(`[menu-labels] 通过：${design.length} 个分组，${design.reduce((n, g) => n + g.items.length, 0)} 个菜单项`)
