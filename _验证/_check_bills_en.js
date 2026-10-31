const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  page.on('pageerror', (e) => console.log('PAGEERR', String(e).slice(0, 200)))
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await page.evaluate(() => localStorage.setItem('bp_locale', 'en-US'))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(900)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('Sign in'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1200)
  await page.goto(BASE + '/#/bills', { waitUntil: 'networkidle2' })
  await sleep(2500)
  console.log('headers:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table__header th')).map((x) => x.innerText.trim()).slice(0, 12)))
  console.log('toolbar:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.toolbar button')).map((x) => x.innerText.trim()).slice(0, 12)))
  console.log('status sample:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table__body td')).map((x) => x.innerText.trim()).find((x) => x)))
  await page.screenshot({ path: '_验证/i18n_bills_en.png' })
  await b.close()
})()
