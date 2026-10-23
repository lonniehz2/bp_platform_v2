/**
 * 能耗分析弹窗冒烟：打开账单页 → 点「能耗分析」→ 检查表格数据行数。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')
const fs = require('fs')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const shots = path.join(__dirname, '_shots')
fs.mkdirSync(shots, { recursive: true })

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })

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
  await page.goto(BASE + '/#/bills', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 1800))

  const btn = await page.$('[data-testid="bill-energy"]')
  if (!btn) { console.log('结论：未找到能耗分析按钮'); await browser.close(); process.exit(1) }
  await btn.click()
  await new Promise(r => setTimeout(r, 2000))

  const info = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog')).pop()
    if (!dlg) return null
    const rows = dlg.querySelectorAll('.el-table__body tr').length
    const title = dlg.querySelector('.el-dialog__title')?.innerText.trim()
    const headers = Array.from(dlg.querySelectorAll('.el-table__header th'))
      .map(e => e.innerText.trim()).filter(Boolean)
    return { title, rows, headers: headers.slice(0, 8) }
  })
  await page.screenshot({ path: path.join(shots, 'energy.png') })
  console.log('弹窗:', info && info.title, ' 表格行数:', info && info.rows)
  console.log('表头:', info && info.headers.join(' / '))
  console.log(info && info.rows > 0 ? '结论：能耗分析有数据' : '结论：能耗分析为空（异常）')
  await browser.close()
  process.exit(info && info.rows > 0 ? 0 : 1)
})()
