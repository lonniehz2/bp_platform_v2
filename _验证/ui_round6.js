const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1600, height: 1000 })
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
    if (b) b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)
  await page.evaluate(() => { location.hash = '#/bills' })
  await sleep(4500)

  // 勾选第一行
  await page.evaluate(() => {
    const cb = document.querySelector('.el-table__body .el-checkbox__original')
    const box = document.querySelector('.el-table__body .el-checkbox')
    if (box) box.click()
    else if (cb) cb.click()
  })
  await sleep(600)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('批量催缴'))
    if (b) b.click()
  })
  await sleep(2000)
  console.log('批量催缴消息:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message')).map(x => x.innerText.trim()))))

  // 批量出账：组织选项
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('批量出账'))
    if (b) b.click()
  })
  await sleep(1500)
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    const w = d && d.querySelector('.el-select__wrapper')
    if (w) { w.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); w.click() }
  })
  await sleep(1200)
  console.log('组织选项数:', await page.evaluate(() => document.querySelectorAll('.el-select-dropdown__item').length))
  await browser.close()
})()
