const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const PAGES = ['#/devices', '#/grants', '#/fee-items', '#/ops-extras']
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1000 })
  await page.setCacheEnabled(false)
  const errors = []
  page.on('pageerror', (e) => errors.push(String(e).slice(0, 160)))
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
  for (const hash of PAGES) {
    errors.length = 0
    await page.evaluate((h) => { location.hash = h }, hash)
    await sleep(2800)
    const info = await page.evaluate(() => ({
      title: document.querySelector('h3')?.innerText,
      selects: document.querySelectorAll('.toolbar .el-select').length,
      idInputs: Array.from(document.querySelectorAll('input'))
        .filter((x) => (x.placeholder || '').includes('ID')).length
    }))
    console.log(hash, JSON.stringify(info), '错误:', errors.length ? errors[0] : '无')
  }
  await browser.close()
})()
