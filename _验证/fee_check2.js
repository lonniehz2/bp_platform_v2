// 校验规则集「域/场景」中文与计费下拉项
const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1300 })
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
  await sleep(2600)

  await page.evaluate(() => { location.hash = '#/alerts' })
  await sleep(3800)
  const rows = await page.evaluate(() => {
    const c = Array.from(document.querySelectorAll('.page-card'))
      .find((x) => (x.querySelector('h4')?.innerText || '').includes('规则引擎'))
    if (!c) return []
    const tables = c.querySelectorAll('.el-table')
    const t = tables[tables.length - 2] || tables[0]
    return Array.from(t.querySelectorAll('.el-table__body tr')).slice(0, 4)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 90))
  })
  console.log('规则集行:', JSON.stringify(rows))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'rules-domain2.png') })

  // 计费项目：费用类型下拉项
  await page.evaluate(() => { location.hash = '#/fee-items' })
  await sleep(3200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新增项目'))
    if (b) b.click()
  })
  await sleep(1200)
  const opts = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return []
    const sel = d.querySelectorAll('.el-select')[0]
    sel.querySelector('.el-select__wrapper')?.click()
    return []
  })
  await sleep(900)
  const types = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-select-dropdown__item'))
      .map((x) => x.innerText.trim()).slice(0, 12))
  console.log('费用类型下拉:', JSON.stringify(types))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'fee-types-dropdown.png') })
  await browser.close()
})()
