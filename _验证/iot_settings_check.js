// 系统参数页：IoT 对接参数卡片
const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1200 })
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
  await sleep(2400)

  await page.evaluate(() => { location.hash = '#/sys/config' })
  await sleep(3500)
  // 切到「系统参数」页签
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-tabs__item'))
      .find((x) => x.innerText.includes('系统参数'))
    if (t) t.click()
  })
  await sleep(2000)

  const info = await page.evaluate(() => {
    const card = Array.from(document.querySelectorAll('.el-card'))
      .find((c) => (c.innerText || '').includes('IoT 对接参数'))
    if (!card) return { ok: false }
    const rows = Array.from(card.querySelectorAll('.el-table__body tr'))
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 90))
    return { ok: true, title: 'IoT 对接参数', rows }
  })
  console.log('IoT 参数卡片:', info.ok, '行数', info.rows ? info.rows.length : 0)
  if (info.rows) info.rows.slice(0, 3).forEach((r) => console.log('  ', r))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'iot-settings.png') })
  await browser.close()
})()
