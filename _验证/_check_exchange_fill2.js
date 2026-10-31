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
  await page.goto(BASE + '/#/exchanges', { waitUntil: 'networkidle2' })
  await sleep(2500)
  const opened = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建换房'))
    if (btn) { btn.click(); return true }
    return false
  })
  await sleep(800)
  console.log('dialog opened', opened)
  // 人员选择器输入
  console.log('inputs', await page.evaluate(() => Array.from(document.querySelectorAll('.el-dialog input')).map((i) => i.placeholder)))
  const input = await page.$('[data-testid="person-picker"] input')
  if (input) {
    await input.click()
    await input.type('b66', { delay: 80 })
    await sleep(1500)
    const opts = await page.evaluate(() =>
      Array.from(document.querySelectorAll('.el-select-dropdown__item')).map((x) => x.innerText.trim()))
    console.log('options', JSON.stringify(opts.slice(0, 5)))
    await page.evaluate(() => {
      const o = document.querySelector('.el-select-dropdown__item')
      if (o) o.click()
    })
    await sleep(2000)
    console.log('fields', await page.evaluate(() => {
      const q = (id) => document.querySelector(`[data-testid="${id}"] input`)?.value
      return { contract: q('f-oldContractId'), house: q('f-oldHouseId') }
    }))
  }
  await page.screenshot({ path: '_验证/exchange_autofill.png' })
  await b.close()
})()
