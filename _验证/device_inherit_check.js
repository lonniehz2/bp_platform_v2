/**
 * 继承设备页签视觉验证：截图 + 读取设备表文本。
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
  await new Promise(r => setTimeout(r, 2200))

  await page.evaluate(() => document.querySelector('.el-table__body tr').click())
  await new Promise(r => setTimeout(r, 1500))

  const readDeviceTable = async () => page.evaluate(() => {
    // 右侧设备表：取包含「设备名称」表头的那张表
    const tables = Array.from(document.querySelectorAll('.el-table'))
    const t = tables.find((x) => (x.innerText || '').includes('设备名称'))
    if (!t) return []
    return Array.from(t.querySelectorAll('.el-table__body tr'))
      .map((tr) => tr.innerText.replace(/\n+/g, ' | ').trim())
  })

  const own = await readDeviceTable()
  console.log('本房源页签：')
  own.forEach((r) => console.log('   ' + r))

  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-tabs__item'))
      .find((x) => x.innerText.includes('继承'))
    t && t.click()
  })
  await new Promise(r => setTimeout(r, 1800))
  const inherit = await readDeviceTable()
  console.log('继承页签：')
  inherit.forEach((r) => console.log('   ' + r))

  await page.screenshot({ path: path.join(shots, 'device-inherit.png') })
  const leaked = inherit.filter((r) => r.includes('1205室'))
  console.log(leaked.length ? '✗ 继承页签仍含本房源设备' : '✔ 继承页签不含本房源设备')
  await browser.close()
  process.exit(leaked.length ? 1 : 0)
})()
