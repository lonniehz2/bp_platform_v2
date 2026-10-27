const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const csv = path.join(__dirname, '_device_import.csv')
  fs.writeFileSync(csv, '设备编号,设备名称,设备类型,设备MAC,房源编号\n'
    + 'UI-IMP-1,UI导入门锁,门锁,AA:BB:CC:11:11:01,H8063501\n'
    + 'UI-IMP-2,UI导入水表,水表,AA:BB:CC:11:11:02,\n', 'utf8')

  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1000 })
  await page.setCacheEnabled(false)
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2200)
  await page.evaluate(() => { location.hash = '#/devices' })
  await sleep(3200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('批量导入'))
    if (b) b.click()
  })
  await sleep(1500)
  const input = await page.$('.el-dialog input[type=file]')
  if (input) await input.uploadFile(csv)
  await sleep(1800)
  const preview = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return {
      steps: Array.from(d.querySelectorAll('.el-step__title')).map((x) => x.innerText.trim()),
      alert: d.querySelector('.el-alert__title')?.innerText,
      rows: d.querySelectorAll('.el-table__body tr').length
    }
  })
  console.log('预览:', JSON.stringify(preview))
  // 开始导入
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const b = Array.from(d.querySelectorAll('button')).find((x) => x.innerText.includes('开始导入'))
    if (b) b.click()
  })
  await sleep(4000)
  const result = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return { alert: d.querySelector('.el-alert__title')?.innerText,
      rows: d.querySelectorAll('.el-table__body tr').length }
  })
  console.log('结果:', JSON.stringify(result))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'device-import.png') })
  await browser.close()
})()
