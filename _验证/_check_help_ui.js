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
  await page.goto(BASE + '/#/help', { waitUntil: 'networkidle2' })
  await sleep(2500)
  console.log('toc:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.toc-item')).map((x) => x.innerText.trim()).slice(0, 15)))
  console.log('h2:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.sec h2')).map((x) => x.innerText.trim()).slice(0, 5)))
  console.log('formulas:', await page.evaluate(() => document.querySelectorAll('.formula').length))
  console.log('faq:', await page.evaluate(() => document.querySelectorAll('.faq .el-collapse-item').length))
  const pdfBtn = await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).some((x) => x.innerText.includes('下载 PDF')))
  console.log('pdf button:', pdfBtn)
  await page.screenshot({ path: '_验证/help_online.png' })
  await b.close()
})()
