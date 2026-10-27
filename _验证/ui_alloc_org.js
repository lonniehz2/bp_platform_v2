const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
  await page.setCacheEnabled(false)
  page.on('console', (m) => { if (m.type() === 'error') console.log('控制台错误:', m.text().slice(0, 200)) })
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
  await page.evaluate(() => { location.hash = '#/allocations' })
  await sleep(3000)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建批次'))
    if (b) b.click()
  })
  await sleep(3000)
  // 点击「项目组织」选择框
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const items = Array.from(d.querySelectorAll('.el-form-item'))
    const target = items.find((x) => x.innerText.includes('项目组织'))
    const wrapper = target && target.querySelector('.el-select__wrapper')
    if (wrapper) wrapper.click()
  })
  await sleep(1500)
  const opts = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-select-dropdown__item'))
      .map((x) => x.innerText.trim()).filter(Boolean).slice(0, 6))
  console.log('项目组织下拉项:', JSON.stringify(opts))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'alloc-org-dropdown.png') })
  await browser.close()
})()
