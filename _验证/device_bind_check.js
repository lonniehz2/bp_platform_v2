/**
 * 设备绑定页检查：选房源 → 看设备 → 打开绑定弹窗。
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
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)

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
  await page.goto(BASE + '/#/device-bind', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))

  // 选中第一行房源
  await page.evaluate(() => {
    const row = document.querySelector('.el-table__body tr')
    row && row.click()
  })
  await new Promise(r => setTimeout(r, 1500))

  // 打开绑定弹窗
  const opened = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button'))
      .find((b) => b.innerText.trim() === '绑定设备')
    if (btn) { btn.click(); return true }
    return false
  })
  await new Promise(r => setTimeout(r, 1800))

  const info = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog')).pop()
    return {
      dialog: !!dlg,
      rows: dlg ? dlg.querySelectorAll('.el-table__body tr').length : 0,
      header: (document.querySelector('.el-card__body') || {}).innerText?.slice(0, 60) || ''
    }
  })
  await page.screenshot({ path: path.join(shots, 'device-bind.png') })
  console.log('打开弹窗:', opened, ' 弹窗行数:', info.rows)
  console.log(info.rows > 0 ? '结论：可选择未绑定设备' : '结论：无未绑定设备可选')
  await browser.close()
  process.exit(info.rows > 0 ? 0 : 1)
})()
