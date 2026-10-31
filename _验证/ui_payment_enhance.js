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

  // 登记收款弹窗：应有收款时间
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.trim() === '登记收款')
    if (x) x.click()
  })
  await sleep(1000)
  console.log('收款时间字段:', await page.evaluate(() => document.body.innerText.includes('收款时间')))
  await page.keyboard.press('Escape'); await sleep(400)

  // 收款单
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.trim() === '收款单')
    if (x) x.click()
  })
  await sleep(1800)
  console.log('收款单:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    const op = d.querySelector('th:last-child')
    return { width: d.getBoundingClientRect().width,
      ops: Array.from(d.querySelectorAll('.el-table__body tr:first-child button')).map((b) => b.innerText.trim()),
      opCol: op && op.innerText.trim() }
  })))
  // 详情
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('.el-table__body button')).find((t) => t.innerText.trim() === '详情')
    if (x) x.click()
  })
  await sleep(1500)
  console.log('详情弹窗:', await page.evaluate(() => document.body.innerText.includes('使用明细')))
  await page.keyboard.press('Escape'); await sleep(400)
  // 核销到账单
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('.el-table__body button')).find((t) => t.innerText.trim() === '核销到账单')
    if (x) x.click()
  })
  await sleep(1500)
  console.log('核销到账单:', await page.evaluate(() => document.body.innerText.includes('目标账单')))
  await page.keyboard.press('Escape'); await sleep(400)
  // 账单详情
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('.el-table__body button')).find((t) => t.innerText.trim() === '详情')
    if (x) x.click()
  })
  await sleep(1500)
  console.log('账单详情缴费明细:', await page.evaluate(() => document.body.innerText.includes('缴费明细')))
  await b.close()
})()
