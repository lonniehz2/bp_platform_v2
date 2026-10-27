const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
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

  // 配租页面：点批次行
  await page.evaluate(() => { location.hash = '#/allocations' })
  await sleep(3500)
  const headers = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table__header th')).map((x) => x.innerText.trim()))
  console.log('表头:', JSON.stringify(headers.slice(0, 14)))
  await page.evaluate(() => {
    const row = document.querySelector('.el-table__body tr')
    if (row) row.click()
  })
  await sleep(2000)
  const after = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.page-card'))
    const bottom = cards[cards.length - 1]
    return { title: bottom.querySelector('h3')?.innerText,
      batch: bottom.innerText.match(/当前批次：[^\n]*/)?.[0] || '',
      rows: bottom.querySelectorAll('.el-table__body tr').length }
  })
  console.log('批次联动:', JSON.stringify(after))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'alloc-batch-filter.png') })

  // 系统参数修改
  await page.evaluate(() => { location.hash = '#/sys/config' })
  await sleep(3000)
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-tabs__item')).find((x) => x.innerText.includes('系统参数'))
    if (t) t.click()
  })
  await sleep(2500)
  const cfg = await page.evaluate(() => ({
    rows: document.querySelectorAll('.el-table__body tr').length,
    hasEdit: !!document.querySelector('[data-testid="sys-config-edit"]')
  }))
  console.log('系统参数:', JSON.stringify(cfg))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'sys-config-edit.png') })

  await browser.close()
})()
