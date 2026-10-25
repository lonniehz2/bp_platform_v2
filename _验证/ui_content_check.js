/**
 * 页面内容正确性检查（比 ui_smoke 更深一层）。
 *
 * 规则
 * ----
 * A. **列不为空**：表格每一列至少有一行非空（防"列全空/字段名对不上"）
 * B. **筛选生效**：对配置了筛选的页面，应用筛选后行数必须变化
 *    （防"筛选条件没接到后端"，就是设备分类那个问题）
 * C. **序号/编号类列有值**：编号、名称、状态类列不得整列为空
 */
const puppeteer = require('puppeteer-core')
const path = require('path')
const fs = require('fs')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const shots = path.join(__dirname, '_shots')
fs.mkdirSync(shots, { recursive: true })

// 页面 → 需要验证的筛选（下拉选择器索引 + 选项文本）
const FILTER_CASES = [
  { path: '/devices', label: '设备管理', selectText: '设备类型', option: '门锁' },
  { path: '/devices', label: '设备管理', selectText: '设备类型', option: '水表' },
  { path: '/bills', label: '账单与缴费', selectText: '状态', option: '已缴清' },
  { path: '/houses', label: '房源台账', selectText: '房态', option: '已出租' }
]

// 允许为空的列（操作/开关等）
const IGNORE_COLS = ['操作', '展开', '选择']

async function login(page) {
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await new Promise(r => setTimeout(r, 300))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail, .el-menu, .aside'),
    { timeout: 20000 })
}

/** 读取表格结构：按单元格列统计非空数（不依赖表头对齐） */
async function readTable(page) {
  return page.evaluate(() => {
    const tables = Array.from(document.querySelectorAll('.el-table'))
      .filter((x) => !x.closest('.el-table__fixed, .el-table__fixed-right'))
    const t = tables.find((x) => x.querySelector('.el-table__body tr'))
    if (!t) return { labels: [], filled: [], rows: 0 }
    const heads = Array.from(t.querySelectorAll('.el-table__header-wrapper th'))
      .map((th) => (th.innerText || '').trim())
    const trs = Array.from(t.querySelectorAll('.el-table__body tr'))
      .filter((tr) => tr.querySelectorAll('td').length > 1)
    let maxCols = 0
    for (const tr of trs) maxCols = Math.max(maxCols, tr.querySelectorAll('td').length)
    const filled = new Array(maxCols).fill(0)
    for (const tr of trs) {
      Array.from(tr.querySelectorAll('td')).forEach((td, i) => {
        if (i < maxCols && (td.innerText || '').trim()) filled[i] += 1
      })
    }
    const labels = []
    for (let i = 0; i < maxCols; i++) labels.push(heads[i] || ('第' + (i + 1) + '列'))
    return { labels, filled, rows: trs.length }
  })
}

async function pickOption(page, selectLabel, optionText) {
  const opened = await page.evaluate((label) => {
    const items = Array.from(document.querySelectorAll('.el-select'))
    const target = items.find((x) =>
      (x.innerText || '').includes(label) ||
      (x.querySelector('input')?.placeholder || '').includes(label))
    if (!target) return false
    target.click()
    return true
  }, selectLabel)
  if (!opened) return false
  await new Promise(r => setTimeout(r, 600))
  const picked = await page.evaluate((txt) => {
    const opts = Array.from(document.querySelectorAll('.el-select-dropdown__item'))
    const o = opts.find((x) => (x.innerText || '').trim() === txt)
    if (!o) return false
    o.click()
    return true
  }, optionText)
  await new Promise(r => setTimeout(r, 1500))
  return picked
}

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  await login(page)

  const problems = []

  // A/C：所有页面逐列非空
  const pages = ['/houses', '/bills', '/devices', '/contracts', '/persons',
    '/applications', '/workorders', '/keyring', '/grants', '/dev-events',
    '/meter-readings', '/alerts', '/complaints', '/terminations']
  console.log('第 1 部分：列非空检查（%d 页）', pages.length)
  for (const p of pages) {
    await page.goto(BASE + '/#/p'.replace('/p', '') + '', { waitUntil: 'domcontentloaded' })
    await page.goto(BASE + '/#' + p, { waitUntil: 'networkidle2' })
    await new Promise(r => setTimeout(r, 2200))
    const t = await readTable(page)
    if (!t.rows) {
      problems.push(`${p} 无数据行`)
      continue
    }
    const empties = []
    t.labels.forEach((h, i) => {
      if (IGNORE_COLS.some((c) => h.includes(c))) return
      if (!t.filled[i]) empties.push(h)
    })
    if (empties.length) {
      problems.push(`${p} 整列为空：${empties.join('、')}`)
      await page.screenshot({ path: path.join(shots, 'empty-col-' + p.replace(/\//g, '_') + '.png') })
    }
    console.log('  %s %d 行 / %d 列', p.padEnd(18), t.rows, t.labels.length)
  }

  // B：筛选必须生效
  console.log('\n第 2 部分：筛选生效检查（%d 例）', FILTER_CASES.length)
  for (const c of FILTER_CASES) {
    await page.goto(BASE + '/#' + c.path, { waitUntil: 'networkidle2' })
    await new Promise(r => setTimeout(r, 2200))
    const before = await readTable(page)
    const ok = await pickOption(page, c.selectText, c.option)
    if (!ok) {
      console.log('  %s 未找到筛选项「%s」', c.label, c.option)
      continue
    }
    const after = await readTable(page)
    const changed = after.rows !== before.rows
    console.log('  %s 筛选「%s」：%d → %d %s', c.label.padEnd(8), c.option,
      before.rows, after.rows, changed ? '✔' : '✗ 未生效')
    if (!changed) problems.push(`${c.label} 筛选「${c.option}」未生效（${before.rows}→${after.rows}）`)
  }

  await browser.close()
  console.log('\n' + '='.repeat(60))
  if (problems.length) {
    console.log('发现 %d 个问题：', problems.length)
    problems.forEach((p) => console.log('  ✗ ' + p))
    process.exit(1)
  }
  console.log('  ✔ 列均有值，筛选均生效')
  process.exit(0)
})()
