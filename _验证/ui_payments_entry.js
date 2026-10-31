const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1500, height: 900 })
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
  console.log('按钮:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).some((x) => x.innerText.trim() === '收款单')))
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.trim() === '收款单')
    if (x) x.click()
  })
  await sleep(1800)
  console.log('收款单弹窗:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return d ? { title: d.querySelector('.el-dialog__title')?.innerText,
      heads: Array.from(d.querySelectorAll('th')).map((t) => t.innerText.trim()).filter(Boolean),
      rows: d.querySelectorAll('.el-table__body tr').length,
      total: (d.querySelector('.el-pagination__total') || {}).innerText } : null
  })))
  await page.keyboard.press('Escape')
  await sleep(500)
  // 打开第一行核销
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('.el-table__body tr button'))
      .find((t) => t.innerText.trim() === '核销')
    if (x) x.click()
  })
  await sleep(1500)
  console.log('核销弹窗:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return d ? { text: d.innerText.slice(0, 90).replace(/\n/g, ' | '),
      selects: d.querySelectorAll('.el-select').length } : null
  })))
  await b.close()
})()
