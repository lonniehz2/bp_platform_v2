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
  await page.evaluate(() => localStorage.removeItem('bp_locale'))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(1200)
  console.log('zh brand:', await page.evaluate(() => document.querySelector('h1')?.innerText))
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((b) => b.innerText.trim() === '中文')
    if (x) x.click()
  })
  await sleep(400)
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.el-dropdown-menu__item'))
    const en = items.find((x) => x.innerText.trim() === 'English')
    if (en) en.click()
  })
  await sleep(900)
  console.log('en brand:', await page.evaluate(() => document.querySelector('h1')?.innerText))
  console.log('en welcome:', await page.evaluate(() => document.querySelector('.card-head h2')?.innerText))
  console.log('en placeholders:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.card input')).map((x) => x.placeholder)))
  console.log('en button:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).map((x) => x.innerText.trim()).find((x) => x.includes('Sign'))))
  await page.screenshot({ path: '_验证/i18n_login_en.png' })
  // 切回中文
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((b) => b.innerText.trim() === 'EN')
    if (x) x.click()
  })
  await sleep(400)
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.el-dropdown-menu__item'))
    const zh = items.find((x) => x.innerText.includes('简体中文'))
    if (zh) zh.click()
  })
  await sleep(600)
  await b.close()
})()
