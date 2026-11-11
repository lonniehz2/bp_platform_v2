import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('..', import.meta.url))
globalThis.location = { search: '' }
globalThis.localStorage = { getItem: () => null, setItem: () => {} }
const { messages } = await import('../src/i18n.js')

const flatten = (obj, prefix = '', out = {}) => {
  for (const [key, value] of Object.entries(obj || {})) {
    const path = prefix ? `${prefix}.${key}` : key
    if (value && typeof value === 'object') flatten(value, path, out)
    else out[path] = value
  }
  return out
}
const zh = flatten(messages['zh-CN'])
const en = flatten(messages['en-US'])
const zhKeys = new Set(Object.keys(zh))
const enKeys = new Set(Object.keys(en))
const cjk = /[\u4e00-\u9fa5]/
const allowedChinese = new Set()
let failed = false
for (const key of enKeys) {
  if (cjk.test(String(en[key])) && !allowedChinese.has(key)) {
    console.error(`[i18n:en] ${key} 的英文值包含中文：${en[key]}`)
    failed = true
  }
}
for (const key of zhKeys) {
  if (!enKeys.has(key)) { console.error(`[i18n:en] 缺少英文词条：${key}`); failed = true }
}
for (const key of enKeys) {
  if (!zhKeys.has(key)) { console.error(`[i18n:en] 缺少中文词条：${key}`); failed = true }
}

const sources = []
for (const dir of ['src/pages', 'src/components']) {
  for (const name of readdirSync(join(root, dir))) {
    if (name.endsWith('.vue')) sources.push({ file: `${dir}/${name}`, text: readFileSync(join(root, dir, name), 'utf8') })
  }
}
for (const name of ['App.vue']) sources.push({ file: `src/${name}`, text: readFileSync(join(root, 'src', name), 'utf8') })
const main = readFileSync(join(root, 'src/main.js'), 'utf8')
const used = new Set()
for (const { file, text } of sources) {
  for (const m of text.matchAll(/\bt\(\s*['"]([^'"]+)['"]/g)) used.add(m[1])
  for (const m of text.matchAll(/\bte\(\s*`([^`$]+)`/g)) used.add(m[1])
}
for (const m of main.matchAll(/titleKey:\s*'([^']+)'/g)) used.add(m[1])
for (const key of used) {
  if (key.endsWith('.') || key === 'nav.') continue
  if (!zhKeys.has(key) || !enKeys.has(key)) {
    console.error(`[i18n:en] 页面使用的词条不存在：${key}`)
    failed = true
  }
}
if (failed) process.exit(1)
console.log(`[i18n:en] 通过：${enKeys.size} 个英文词条，${used.size} 个页面词条引用，中英文一致`)
