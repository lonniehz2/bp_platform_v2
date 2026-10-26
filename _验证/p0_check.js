/**
 * P0 验证：催缴（欠费处置/催缴通知）、退租动作按钮、工单动作按钮、告警改名。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function login(page) {
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
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
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2400)
}

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1040 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 170)))

  await login(page)

  // 1) 催缴管理
  await page.evaluate(() => { location.hash = '#/arrears' })
  await sleep(2600)
  const arr = await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('.el-radio-button__inner'))
      .map((x) => x.innerText.trim())
    const rows = Array.from(document.querySelectorAll('.el-table__body tr')).slice(0, 2)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 100))
    const btns = Array.from(document.querySelectorAll('.page-card button'))
      .map((b) => b.innerText.trim()).filter(Boolean)
    return { tabs, rows, btns: Array.from(new Set(btns)).slice(0, 12) }
  })
  console.log('催缴页 页签:', arr.tabs.join(' / '))
  console.log('催缴页 按钮:', arr.btns.join(' | '))
  console.log('催缴页 首行:', arr.rows[0] || '无')
  await page.screenshot({ path: path.join(OUT, 'p0-arrears.png') })

  // 扫描建议
  const scanned = await page.evaluate(async () => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('扫描建议'))
    if (b) { b.click(); return true }
    return false
  })
  await sleep(2400)
  const scanInfo = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog')).find((d) => d.offsetParent)
    return { title: dlg?.querySelector('.el-dialog__title')?.innerText,
      rows: dlg?.querySelectorAll('.el-table__body tr').length }
  })
  console.log('扫描建议弹窗:', scanned, scanInfo.title, '行数', scanInfo.rows)
  await page.screenshot({ path: path.join(OUT, 'p0-arrears-scan.png') })

  // 2) 退租
  await page.evaluate(() => { location.hash = '#/terminations' })
  await sleep(2500)
  const term = await page.evaluate(() => {
    const row = document.querySelector('.el-table__body tr')
    const btns = row ? Array.from(row.querySelectorAll('button')).map((b) => b.innerText.trim()) : []
    return { btns }
  })
  console.log('退租行操作:', term.btns.join(' / '))
  await page.screenshot({ path: path.join(OUT, 'p0-terminations.png') })

  // 3) 工单
  await page.evaluate(() => { location.hash = '#/workorders' })
  await sleep(2500)
  const wo = await page.evaluate(() => {
    const row = document.querySelector('.el-table__body tr')
    const btns = row ? Array.from(row.querySelectorAll('button')).map((b) => b.innerText.trim()) : []
    return { btns }
  })
  console.log('工单行操作:', wo.btns.join(' / '))
  await page.screenshot({ path: path.join(OUT, 'p0-workorders.png') })

  // 4) 告警
  await page.evaluate(() => { location.hash = '#/alerts' })
  await sleep(2400)
  const al = await page.evaluate(() => {
    const row = document.querySelector('.el-table__body tr')
    return { title: document.querySelector('.page-card h3')?.innerText.trim(),
      btns: row ? Array.from(row.querySelectorAll('button')).map((b) => b.innerText.trim()) : [] }
  })
  console.log('告警页 标题:', al.title, '| 行操作:', al.btns.join(' / '))
  await page.screenshot({ path: path.join(OUT, 'p0-alerts.png') })

  await browser.close()
})()
