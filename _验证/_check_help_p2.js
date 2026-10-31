const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
async function login(page) {
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(700)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('登'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1200)
}
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  page.on('pageerror', (e) => console.log('PAGEERR', String(e).slice(0, 200)))
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  await login(page)
  await page.goto(BASE + '/#/help?sec=ch6', { waitUntil: 'networkidle2' })
  await sleep(2200)
  console.log('active:', await page.evaluate(() =>
    document.querySelector('.toc-item.active')?.innerText.trim()))
  console.log('subs:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.toc-sub')).map((x) => x.innerText.trim())))
  await page.evaluate(() => {
    const subs = document.querySelectorAll('.toc-sub')
    if (subs[3]) subs[3].click()
  })
  await sleep(900)
  console.log('active sub:', await page.evaluate(() =>
    document.querySelector('.toc-sub.active')?.innerText.trim()))
  const input = await page.$('.search-input input')
  await input.type('核销')
  await sleep(700)
  console.log('marks:', await page.evaluate(() => document.querySelectorAll('mark').length))
  await page.screenshot({ path: '_验证/help_p2_desktop.png' })
  await page.setViewport({ width: 390, height: 844 })
  await page.goto(BASE + '/#/help', { waitUntil: 'networkidle2' })
  await sleep(1800)
  console.log('mobile toc hidden:', await page.evaluate(() => {
    const el = document.querySelector('.toc-col')
    return el ? getComputedStyle(el).display === 'none' : true
  }))
  console.log('mobile select:', await page.evaluate(() => {
    const el = document.querySelector('.mobile-toc-select')
    return el ? getComputedStyle(el).display !== 'none' : false
  }))
  console.log('mobile overflow:', await page.evaluate(() =>
    document.documentElement.scrollWidth + '/' + window.innerWidth))
  console.log('help page width:', await page.evaluate(() => {
    const el = document.querySelector('.help-page')
    return el ? Math.round(el.getBoundingClientRect().width) : 0
  }))
  await page.screenshot({ path: '_验证/help_p2_mobile.png' })
  await b.close()
})()
