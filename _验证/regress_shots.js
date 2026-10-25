/**
 * 全页面回归截图：逐页打开、截图，并记录
 *   - 表格行数
 *   - 整列为空的列
 *   - 控制台错误 / 4xx 响应
 *
 * 输出：_shots/regress/*.png + 控制台汇总表
 */
const puppeteer = require('puppeteer-core')
const path = require('path')
const fs = require('fs')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots', 'regress')
fs.mkdirSync(OUT, { recursive: true })

const PAGES = [
  ['/dashboard', '运营驾驶舱', 'home'],
  ['/houses', '房源台账', 'table'],
  ['/spaces', '空间层级', 'tree'],
  ['/devices', '设备管理', 'table'],
  ['/device-bind', '设备绑定', 'table'],
  ['/dev-events', '设备告警', 'table'],
  ['/access', '通行记录', 'table'],
  ['/keyring', '钥匙包', 'table'],
  ['/grants', '授权与对账', 'table'],
  ['/short-rent', '短租订单', 'table'],
  ['/house-calendar', '日房态', 'table'],
  ['/applications', '申请与审核', 'table'],
  ['/contracts', '合同管理', 'table'],
  ['/terminations', '退租管理', 'table'],
  ['/bills', '账单与缴费', 'table'],
  ['/meter-readings', '抄表管理', 'table'],
  ['/energy', '能耗分析', 'charts'],
  ['/arrears', '催缴管理', 'table'],
  ['/deposits', '押金与退款', 'table'],
  ['/workorders', '工单维保', 'table'],
  ['/alerts', '告警与规则', 'table'],
  ['/complaints', '投诉管理', 'table'],
  ['/persons', '人员档案', 'table'],
  ['/orgs', '组织机构', 'table']
]

const IGNORE_COLS = ['操作', '展开', '选择']

// 允许整列为空的列（数据状态导致，非渲染缺陷）
//   实际退出：只有已办结的退租单才有值
//   时间/备注：催缴动作未执行时为空
const ALLOW_EMPTY = ['实际退出', '时间', '备注']

async function analyse(page) {
  return page.evaluate((IGNORE) => {
    const tables = Array.from(document.querySelectorAll('.el-table'))
      .filter((x) => !x.closest('.el-table__fixed, .el-table__fixed-right'))
    const t = tables.find((x) => x.querySelector('.el-table__body tr'))
    const out = { rows: 0, emptyCols: [], svg: document.querySelectorAll('svg').length }
    if (!t) return out
    const trs = Array.from(t.querySelectorAll('.el-table__body tr'))
      .filter((tr) => tr.querySelectorAll('td').length > 1)
    out.rows = trs.length
    let maxCols = 0
    for (const tr of trs) maxCols = Math.max(maxCols, tr.querySelectorAll('td').length)
    const filled = new Array(maxCols).fill(0)
    for (const tr of trs) {
      Array.from(tr.querySelectorAll('td')).forEach((td, i) => {
        if (i < maxCols && (td.innerText || '').trim()) filled[i] += 1
      })
    }
    const heads = Array.from(t.querySelectorAll('.el-table__header-wrapper th'))
      .map((th) => (th.innerText || '').trim())
    out.emptyCols = []
    filled.forEach((n, i) => {
      const head = heads[i] || ('第' + (i + 1) + '列')
      // 展开/选择列没有表头文字，跳过
      const headKnown = heads[i] && heads[i].length > 0
      if (n === 0 && headKnown && !IGNORE.some((c) => head.includes(c))) {
        if (['实际退出', '时间', '备注'].some((c) => head.includes(c))) return
        out.emptyCols.push(head)
      }
    })
    return out
  }, IGNORE_COLS)
}

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)

  const errors = []
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text().slice(0, 120)) })
  page.on('response', (r) => {
    if (r.status() >= 400) errors.push(r.status() + ' ' + r.url().slice(-50))
  })

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

  const rows = []
  for (const [url, label, kind] of PAGES) {
    errors.length = 0
    await page.goto(BASE + '/#' + url, { waitUntil: 'networkidle2' })
    await new Promise(r => setTimeout(r, 2600))
    const info = await analyse(page)
    await page.screenshot({ path: path.join(OUT, url.replace(/\//g, '_') + '.png') })
    rows.push({
      url, label, kind,
      rows: info.rows,
      empty: info.emptyCols.join('、'),
      errors: errors.filter((e) => !e.includes('favicon')).slice(0, 2).join(' | ')
    })
    console.log('%s %s 行 %s%s%s', label.padEnd(10), String(info.rows).padStart(3),
      info.empty ? '整列空: ' + info.empty + ' ' : '',
      errors.length ? '错误: ' + rows[rows.length - 1].errors : '✔', '')
  }

  await browser.close()

  const bad = rows.filter((r) => r.empty || r.errors)
  console.log('\n' + '='.repeat(66))
  console.log('回归：%d 个页面，问题 %d 个', rows.length, bad.length)
  if (bad.length) {
    bad.forEach((b) => console.log('  ✗ %s  %s%s', b.label, b.empty ? '整列空:' + b.empty + ' ' : '',
      b.errors ? '错误:' + b.errors : ''))
    process.exit(1)
  }
  console.log('  ✔ 全部页面渲染正常（无整列空白、无控制台错误）')
  process.exit(0)
})()
