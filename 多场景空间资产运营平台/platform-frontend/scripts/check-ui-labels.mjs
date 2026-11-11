import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
globalThis.location = { search: '' }
globalThis.localStorage = { getItem: () => null, setItem: () => {} }
const { messages } = await import('../src/i18n.js')
const { navGroups } = await import('../src/navConfig.js')

const get = (obj, path) => path.split('.').reduce((o, k) => o?.[k], obj)
const zh = messages['zh-CN']
const en = messages['en-US']
let failed = false
const fail = msg => { console.error(`[ui-labels] ${msg}`); failed = true }

const suffix = /\.\w*(?:Status|Type|Level|Priority|Cycle|Mode|Gender|Urgency|Method|Category)\b/
for (const dir of ['src/pages', 'src/components']) {
  for (const name of readdirSync(join(root, dir))) {
    if (!name.endsWith('.vue')) continue
    const file = `${dir}/${name}`
    const text = readFileSync(join(root, file), 'utf8')
    for (const m of text.matchAll(/\{\{\s*([^}]+?)\s*\}\}/g)) {
      const expr = m[1]
      if (!suffix.test(expr)) continue
      if (/enumLabel|statusLabel|Label\(|typeName|cycleName|===|\?|t\(/.test(expr)) continue
      fail(`${file} 直接输出枚举字段：{{ ${expr} }}，请使用 enumLabel`)
    }
  }
}

const expectedGroups = ['workbench', 'application', 'contract', 'asset', 'finance', 'service', 'access', 'risk', 'data', 'system']
const actualGroups = navGroups.map(g => g.key)
if (actualGroups.join(',') !== expectedGroups.join(',')) fail(`navConfig 分组不一致：${actualGroups.join(',')}`)
for (const g of navGroups) {
  for (const lang of ['zh-CN', 'en-US']) if (!get(messages[lang], g.labelKey)) fail(`缺少菜单分组词条：${lang}.${g.labelKey}`)
  for (const item of g.items) {
    for (const lang of ['zh-CN', 'en-US']) if (!get(messages[lang], `nav.${item.key}`)) fail(`缺少菜单词条：${lang}.nav.${item.key}`)
  }
}
if (failed) process.exit(1)
console.log(`[ui-labels] 通过：${navGroups.length} 个菜单分组，枚举渲染无裸字段`)
