const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1600, height: 1000 })
  await page.setCacheEnabled(false)
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
  await sleep(2000)
  const heads = async (hash) => {
    await page.evaluate((h) => { location.hash = h }, hash)
    await sleep(3200)
    return page.evaluate(() => Array.from(document.querySelectorAll('.el-table__header th'))
      .map((x) => x.innerText.trim()).filter(Boolean))
  }
  console.log('公示表头:', JSON.stringify(await heads('#/publicities')))
  console.log('房源表头:', JSON.stringify(await heads('#/houses')))
  console.log('房源入住信息按钮:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).filter((b) => b.innerText.includes('入住信息')).length))
  console.log('配租单签约按钮:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).filter((b) => /签约/.test(b.innerText))
      .map((b) => b.innerText.trim()).slice(0, 3))))
  await browser.close()
})()
