const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  page.on('response', (r) => { if (r.url().includes('/exchanges') && r.request().method() === 'POST') console.log('POST', r.status(), r.url().slice(-60)) })
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(300)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('登'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)
  await page.goto(BASE + '/#/exchanges', { waitUntil: 'networkidle2' })
  await sleep(3000)
  // 更多▾
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('更多'))
    if (btn) btn.click()
  })
  await sleep(600)
  await page.evaluate(() => {
    const item = Array.from(document.querySelectorAll('.el-dropdown-menu__item'))
      .find((x) => x.innerText.trim() === '批准')
    if (item) item.click()
  })
  await sleep(900)
  await page.evaluate(() => {
    const inp = document.querySelector('.el-message-box input')
    if (inp) { inp.focus(); inp.value = '联调批准'; inp.dispatchEvent(new Event('input', { bubbles: true })) }
  })
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('.el-message-box button'))
      .find((x) => x.innerText.includes('确定') || x.innerText.includes('确认'))
    if (btn) btn.click()
  })
  await sleep(2500)
  console.log('toast:', await page.evaluate(() => document.querySelector('.el-message')?.innerText || ''))
  await b.close()
})()
