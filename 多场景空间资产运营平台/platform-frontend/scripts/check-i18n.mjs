import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { execSync } from 'node:child_process'

const root = fileURLToPath(new URL('..', import.meta.url))
const baseline = new Set(JSON.parse(readFileSync(join(root, 'scripts/i18n-baseline.json'), 'utf8')))
const strict = process.argv.includes('--strict')
const changedOnly = process.argv.includes('--changed')
let changed = new Set()
if (changedOnly) {
  try {
    const out = execSync('git diff --name-only HEAD^ HEAD', { encoding: 'utf8' })
    changed = new Set(out.split('\n').map(x => x.trim()).filter(Boolean).map(x => x.replace(/^.*?platform-frontend\//, '')))
  } catch {}
}
const files = []
for (const dir of ['src/pages', 'src/components']) {
  for (const name of readdirSync(join(root, dir))) {
    if (name.endsWith('.vue')) files.push(`${dir}/${name}`)
  }
}
const chinese = /[\u4e00-\u9fa5]/
const scene = /GUARANTEE/
let failed = false
for (const file of files) {
  if (!strict && baseline.has(file) && !changed.has(file)) continue
  const text = readFileSync(join(root, file), 'utf8')
  if (chinese.test(text)) { console.error(`[i18n] ${file}: 新增/修改页面包含硬编码中文`); failed = true }
  if (scene.test(text)) { console.error(`[i18n] ${file}: 新增/修改页面包含硬编码场景 GUARANTEE`); failed = true }
}
if (failed) { console.error('请使用 i18n key 或 sceneRoot/currentScene，不要硬编码中文或 GUARANTEE。'); process.exit(1) }
console.log(`[i18n] 新页面检查通过：${files.length} 个页面/组件，基线 ${baseline.size} 个`)
