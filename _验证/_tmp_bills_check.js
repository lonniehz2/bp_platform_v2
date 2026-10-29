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
    if (b) b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)

  await page.evaluate(() => { location.hash = '#/bills' })
  await sleep(4000)
  console.log('账单按钮:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim())
      .filter(t => t.includes('催缴') || t.includes('批量出账')))))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('批量出账'))
    if (b) b.click()
  })
  await sleep(900)
  console.log('批量出账弹窗:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    return d ? { text: d.innerText.slice(0, 60).replace(/\n/g, ' | '), selects: d.querySelectorAll('.el-select').length } : null
  })))
  await page.keyboard.press('Escape')

  await page.evaluate(() => { location.hash = '#/arrears' })
  await sleep(3500)
  console.log('抄表筛选/选择:', JSON.stringify(await page.evaluate(() => ({
    selects: document.querySelectorAll('.toolbar .el-select').length,
    selections: document.querySelectorAll('.el-table__body .el-checkbox').length,
    batchBill: Array.from(document.querySelectorAll('button')).some(b => b.innerText.includes('批量出账'))
  }))))

  await page.evaluate(() => { location.hash = '#/fee-items' })
  await sleep(3500)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('规则列表'))
    if (b) b.click()
  })
  await sleep(1000)
  console.log('规则过滤:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    return d ? { orgSelect: !!d.querySelector('[data-testid="rule-org"]') ||
      Array.from(d.querySelectorAll('.el-select')).length >= 2,
      heads: Array.from(d.querySelectorAll('th')).map(t => t.innerText.trim()).filter(Boolean) } : null
  })))
  await browser.close()
})()
