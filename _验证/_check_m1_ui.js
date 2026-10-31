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
  await page.goto(BASE + '/#/bills', { waitUntil: 'networkidle2' })
  await sleep(3000)
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('批量出账'))
    if (btn) btn.click()
  })
  await sleep(1200)
  console.log('rule modes:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-dialog .el-radio-button')).map((x) => x.innerText.trim())))
  // 选第一个收费项目
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const item = Array.from(d.querySelectorAll('.el-form-item')).find((x) => x.innerText.includes('收费项目'))
    const inp = item && item.querySelector('input')
    if (inp) inp.click()
  })
  await sleep(700)
  await page.evaluate(() => {
    const o = document.querySelector('.el-select-dropdown__item')
    if (o) o.click()
  })
  await sleep(1200)
  console.log('rules loaded:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-select-dropdown__item')).map((x) => x.innerText.trim()).slice(0, 5)))
  await page.screenshot({ path: '_验证/m1_batch_rule.png' })
  await b.close()
})()
