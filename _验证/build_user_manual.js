/**
 * 由 help.js 生成《用户操作说明》Markdown（单一内容源，避免两处维护）。
 */
const fs = require('fs')
const path = require('path')

const SRC = path.join(__dirname, '..', 'frontend', 'src', 'content', 'help.js')
const OUT = path.join(__dirname, '..', '11_用户操作说明.md')

const raw = fs.readFileSync(SRC, 'utf8')
const body = raw.replace(/export const/g, 'const') + '\nmodule.exports = { HELP_SECTIONS, HELP_VERSION }\n'
const tmp = path.join(__dirname, '_help_tmp.js')
fs.writeFileSync(tmp, body, 'utf8')
const { HELP_SECTIONS, HELP_VERSION } = require(tmp)
fs.unlinkSync(tmp)

const lines = []
lines.push('# 租赁性保障用房管理系统 · 用户操作说明')
lines.push('')
lines.push(`> 版本：${HELP_VERSION}　|　适用角色：管理员、业务经办、财务、房源管理、服务协同、稽核、租户`)
lines.push('')
lines.push('本说明与系统内置「使用帮助」（顶部 ? 图标 / 菜单「系统与集成 → 使用帮助」）内容同源。')
lines.push('')
lines.push('## 目录')
lines.push('')
HELP_SECTIONS.forEach((s) => lines.push(`- ${s.title}`))
lines.push('')

for (const sec of HELP_SECTIONS) {
  lines.push(`## ${sec.title}`)
  lines.push('')
  for (const b of sec.blocks) {
    if (b.type === 'h3') {
      lines.push(`### ${b.text}`)
      lines.push('')
    } else if (b.type === 'p') {
      lines.push(b.text)
      lines.push('')
    } else if (b.type === 'ol') {
      b.items.forEach((it, i) => lines.push(`${i + 1}. ${it}`))
      lines.push('')
    } else if (b.type === 'ul') {
      b.items.forEach((it) => lines.push(`- ${it}`))
      lines.push('')
    } else if (b.type === 'note') {
      lines.push(`> **提示**：${b.text}`)
      lines.push('')
    } else if (b.type === 'table') {
      lines.push('| ' + b.head.join(' | ') + ' |')
      lines.push('|' + b.head.map(() => '---').join('|') + '|')
      b.rows.forEach((r) => lines.push('| ' + r.join(' | ') + ' |'))
      lines.push('')
    }
  }
}

lines.push('---')
lines.push('')
lines.push('如需纸质版：在系统帮助页点击「打印 / 另存 PDF」。')
lines.push('')

fs.writeFileSync(OUT, lines.join('\n'), 'utf8')
console.log('已生成:', OUT)
console.log('章节:', HELP_SECTIONS.length, ' 行数:', lines.length)
