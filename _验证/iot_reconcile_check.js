// IoT 日对账页验证
const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1150 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))

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

  await page.evaluate(() => { location.hash = '#/iot-reconcile' })
  await sleep(3500)
  const info = await page.evaluate(() => ({
    title: document.querySelector('h3')?.innerText,
    cards: Array.from(document.querySelectorAll('.el-card')).slice(0, 3)
      .map((c) => c.innerText.replace(/\s+/g, ' ').trim()),
    tables: Array.from(document.querySelectorAll('.card-title')).map((x) => x.innerText),
    rows: document.querySelectorAll('.el-table__body tr').length
  }))
  console.log('页面:', info.title)
  console.log('卡片:', info.cards.join(' || '))
  console.log('表格:', info.tables.join(' / '), '总行', info.rows)
  await page.screenshot({ path: path.join(__dirname, '_shots', 'iot-reconcile.png') })
  await browser.close()
})()
