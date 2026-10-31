const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
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
  await page.goto(BASE + '/#/help', { waitUntil: 'networkidle2' })
  await sleep(2200)
  const input = await page.$('.toolbar input')
  await input.type('核销')
  await sleep(500)
  console.log('search toc:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.toc-item')).map((x) => x.innerText.trim())))
  await input.click({ clickCount: 3 })
  await page.keyboard.press('Backspace')
  await sleep(400)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('.toc-item'))
      .find((t) => t.innerText.includes('常见问题'))
    if (x) x.click()
  })
  await sleep(600)
  console.log('faq visible:', await page.evaluate(() =>
    document.querySelectorAll('.faq .el-collapse-item').length))
  await page.evaluate(() => {
    const h = document.querySelector('.faq .el-collapse-item__header')
    if (h) h.click()
  })
  await sleep(400)
  console.log('faq answer:', await page.evaluate(() => {
    const a = document.querySelector('.faq .el-collapse-item__content')
    return a ? a.innerText.slice(0, 40) : ''
  }))
  await b.close()
})()
