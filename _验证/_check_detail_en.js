const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
async function login(page) {
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await page.evaluate(() => localStorage.setItem('bp_locale', 'en-US'))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(800)
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
  await sleep(1000)
}
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  await login(page)
  await page.goto(BASE + '/#/contracts', { waitUntil: 'networkidle2' })
  await sleep(2200)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((b) => b.innerText.trim() === 'Detail')
    if (x) x.click()
  })
  await sleep(900)
  console.log('contract detail labels:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-dialog:not([style*="display: none"]) .el-descriptions__label'))
      .map((x) => x.innerText.trim()).slice(0, 20)))
  await page.screenshot({ path: '_验证/i18n_contract_detail_en.png' })
  await page.goto(BASE + '/#/bills', { waitUntil: 'networkidle2' })
  await sleep(2200)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((b) => b.innerText.trim() === 'Detail')
    if (x) x.click()
  })
  await sleep(900)
  console.log('bill detail labels:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-dialog:not([style*="display: none"]) .el-descriptions__label'))
      .map((x) => x.innerText.trim()).slice(0, 16)))
  console.log('bill sections:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-dialog:not([style*="display: none"]) div'))
      .map((x) => x.innerText.trim()).filter((x) => /Payment|Calculation|Raw|Note/.test(x)).slice(0, 6)))
  await page.screenshot({ path: '_验证/i18n_bill_detail_en.png' })
  await b.close()
})()
