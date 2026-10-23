/**
 * 页面数据渲染检查：不只看页面能否打开，还看表格是否真的有内容。
 * 对每个页面统计：行数、每列空值比例；空值率 > 80% 的列视为「疑似字段错配」。
 *
 * 用法：node data_render_check.js
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const shots = path.join(__dirname, '_shots')
fs.mkdirSync(shots, { recursive: true })

// 这些页面应当有数据（一期示范数据）
const PAGES = [
  ['/persons', '人员档案'],
  ['/houses', '房源台账'],
  ['/contracts', '合同管理'],
  ['/bills', '账单与缴费'],
  ['/applications', '申请与审核'],
  ['/workorders', '工单维保'],
  ['/waitlist', '轮候管理'],
  ['/allocations', '配租与摇号'],
  ['/short-rent', '短租订单'],
  ['/appeals', '申诉管理'],
  ['/visits', '走访登记'],
  ['/keyring', '钥匙包'],
  ['/arrears', '催缴管理'],
  ['/deposits', '押金管理']
]

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

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1600, height: 1000 })
  await login(page)

  let problems = 0
  let hardProblems = 0
  for (const [route, name] of PAGES) {
    await page.goto(BASE + '/#' + route, { waitUntil: 'networkidle2' })
    await new Promise(r => setTimeout(r, 1800))
    const stat = await page.evaluate(() => {
      const tables = Array.from(document.querySelectorAll('.el-table'))
      if (!tables.length) return { rows: 0, cols: [], noTable: true }
      // 取行数最多的表
      let best = null
      for (const t of tables) {
        const n = t.querySelectorAll('.el-table__body tr').length
        if (!best || n > best.n) best = { t, n }
      }
      if (!best) return { rows: 0, cols: [], noTable: true }
      const heads = Array.from(best.t.querySelectorAll('.el-table__header th'))
        .map(e => e.innerText.trim())
      const rows = Array.from(best.t.querySelectorAll('.el-table__body tr'))
      const cols = heads.map((h, i) => {
        let empty = 0
        for (const r of rows) {
          const cells = r.querySelectorAll('td')
          const txt = cells[i] ? cells[i].innerText.trim() : ''
          if (!txt || txt === '—' || txt === '-') empty++
        }
        return { head: h, empty, total: rows.length }
      })
      return { rows: rows.length, cols }
    })

    if (stat.noTable) {
      console.log(name.padEnd(10) + ' 无表格（跳过）')
      continue
    }
    if (stat.rows === 0) {
      console.log(name.padEnd(10) + ' 表格为空')
      problems++
      continue
    }
    // 只检查有表头、且有足够行数的列；操作列/序号列常无表头
    const bad = stat.cols.filter(c => c.head && c.head !== '操作'
      && c.total >= 3 && c.empty / c.total > 0.8)
    // 强信号：整列 100% 空且行数 >= 10，几乎必然是字段错配
    const hard = bad.filter(c => c.total >= 10 && c.empty === c.total)
    if (bad.length) {
      problems++
      if (hard.length) hardProblems++
      console.log(name.padEnd(10) + ' 行数 ' + stat.rows + '  ✘ 空列：'
        + bad.map(c => c.head + '(' + c.empty + '/' + c.total + ')').join('、'))
      await page.screenshot({
        path: path.join(shots, 'data-' + route.replace(/\//g, '') + '.png')
      })
    } else {
      console.log(name.padEnd(10) + ' 行数 ' + stat.rows + '  ✔ 各列有值')
    }
  }

  console.log('\n结论：' + (problems === 0 ? '全部页面有数据 ✔' : problems + ' 个页面存在空列/空表'))
  await browser.close()
  process.exit(hardProblems === 0 ? 0 : 1)
})()
