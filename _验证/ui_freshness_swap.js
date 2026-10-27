const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('PAGEERROR', String(e).slice(0, 160)))
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
  await page.evaluate(() => { location.hash = '#/devices' })
  await sleep(3200)
  console.log('设备页提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-alert__title')).map((x) => x.innerText.trim()).slice(0, 2))))
  await page.evaluate(() => { location.hash = '#/contracts' })
  await sleep(3000)
  console.log('合同换床按钮:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).filter((b) => b.innerText.trim() === '换床').length))
  await browser.close()
})()
