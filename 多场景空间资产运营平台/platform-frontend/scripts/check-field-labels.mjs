import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { join } from 'node:path'

const root = fileURLToPath(new URL('..', import.meta.url))
globalThis.location = { search: '' }
globalThis.localStorage = { getItem: () => null, setItem: () => {} }
const { messages } = await import('../src/i18n.js')
const zh = messages['zh-CN'].field || {}
const en = messages['en-US'].field || {}
const service = readFileSync(join(root, '../platform-backend/src/main/java/com/yundao/platform/service/RelationService.java'), 'utf8')
const keys = new Set()
for (const m of service.matchAll(/entity\.put\("([A-Za-z][A-Za-z0-9]*)"/g)) keys.add(m[1])
for (const m of service.matchAll(/select ([\s\S]*?) from /g)) {
  for (const part of m[1].split(',')) {
    const alias = part.trim().match(/(?:^|\s)([a-z][A-Za-z0-9]*)$/)
    if (alias) keys.add(alias[1])
  }
}
for (const key of ['title','subtitle']) keys.add(key)
for (const key of [...keys]) if (/Id$/.test(key) || ['id','type','cnt','c','null','route','payable','relationType','tenant','mainTenantName'].includes(key)) keys.delete(key)
let failed = false
for (const key of [...keys].sort()) {
  if (!zh[key] || !en[key]) { console.error(`[field-labels] 缺少字段词条：field.${key}`); failed = true }
}
if (failed) process.exit(1)
console.log(`[field-labels] 通过：${keys.size} 个详情字段均有中英文词条`)
