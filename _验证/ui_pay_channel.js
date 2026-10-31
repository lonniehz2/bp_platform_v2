const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1600, height: 900 })
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
    const x = Array.from(document.querySelectorAll('button')).find((t) => /登\s*录/.test(t.innerText || ''))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)
  await page.evaluate(() => { location.hash = '#/bills' })
  await sleep(3500)
  // 找一张有缴费记录的账单：打开详情看渠道
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('.el-table__body button')).find((t) => t.innerText.trim() === '详情')
    if (x) x.click()
  })
  await sleep(1500)
  console.log('账单详情渠道文本:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return d ? d.innerText.includes('缴费明细') ? d.innerText.split('缴费明细')[1].slice(0, 120) : '无缴费明细' : null
  })))
  await page.keyboard.press('Escape'); await sleep(400)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.trim() === '收款单')
    if (x) x.click()
  })
  await sleep(1500)
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const x = d && Array.from(d.querySelectorAll('.el-table__body button')).find((t) => t.innerText.trim() === '详情')
    if (x) x.click()
  })
  await sleep(1200)
  console.log('收款单详情渠道:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-dialog')).filter((x) => x.offsetParent)
      .map((x) => (x.innerText.match(/收款渠道[\s\S]{0,20}/) || [''])[0]))))
  await b.close()
})()
