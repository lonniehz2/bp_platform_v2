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
  await sleep(1200)
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
  await sleep(2200)
  console.log('after login url:', await page.evaluate(() => location.hash))
  console.log('header locale button:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).map((x) => x.innerText.trim()).filter((x) => x === 'EN' || x === '中文')))
  console.log('element pagination:', await page.evaluate(() => {
    const x = document.querySelector('.el-pagination__total')
    return x ? x.innerText : ''
  }))
  await page.screenshot({ path: '_验证/i18n_dashboard_en.png' })
  // 切回中文并确认页面不刷新
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((b) => b.innerText.trim() === 'EN')
    if (x) x.click()
  })
  await sleep(300)
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.el-dropdown-menu__item'))
    const zh = items.find((x) => x.innerText.includes('简体中文'))
    if (zh) zh.click()
  })
  await sleep(800)
  console.log('after switch url:', await page.evaluate(() => location.hash))
  console.log('after switch locale button:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).map((x) => x.innerText.trim()).filter((x) => x === 'EN' || x === '中文')))
  await b.close()
})()
