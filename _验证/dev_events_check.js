/**
 * 设备告警弹窗冒烟：打开设备页 → 点「设备告警」→ 检查弹窗表格行数。
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
  await page.goto(BASE + '/#/devices', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 1800))

  const btn = await page.$('[data-testid="dev-events"]')
  if (!btn) { console.log('结论：未找到「设备告警」按钮'); await browser.close(); process.exit(1) }
  await btn.click()
  await new Promise(r => setTimeout(r, 2000))

  const info = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).pop()
    if (!d) return null
    const rows = d.querySelectorAll('.el-table__body tr').length
    const txt = d.innerText.replace(/\n+/g, ' | ').slice(0, 200)
    return { rows, title: d.querySelector('.el-dialog__title')?.innerText.trim(), txt }
  })
  await page.screenshot({ path: path.join(shots, 'dev-events.png') })
  console.log('弹窗:', info && info.title, ' 行数:', info && info.rows)
  console.log('内容片段:', info && info.txt)
  console.log(info && info.rows > 0 ? '结论：设备告警有数据' : '结论：告警为空')
  await browser.close()
  process.exit(info && info.rows > 0 ? 0 : 1)
})()
