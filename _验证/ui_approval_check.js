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
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))
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
  await page.evaluate(() => { location.hash = '#/applications' })
  await sleep(3200)

  // 受理：点第一行「受理」
  const before = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    const row = rows.find((r) => r.innerText.includes('受理'))
    if (!row) return null
    const btn = Array.from(row.querySelectorAll('button')).find((b) => b.innerText.trim() === '受理')
    if (btn) btn.click()
    return row.innerText.replace(/\s+/g, ' ').slice(0, 70)
  })
  console.log('点击受理行:', before)
  await sleep(2500)
  const msgs = await page.evaluate(() => Array.from(document.querySelectorAll('.el-message'))
    .map((x) => x.innerText.trim()))
  console.log('提示:', JSON.stringify(msgs))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'applications-accept.png') })

  // 审核弹窗：阶段应锁定为当前环节
  await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    const row = rows.find((r) => Array.from(r.querySelectorAll('button')).some((b) => b.innerText.trim() === '审核'))
    const btn = row && Array.from(row.querySelectorAll('button')).find((b) => b.innerText.trim() === '审核')
    if (btn) btn.click()
  })
  await sleep(1500)
  const dlg = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    const inputs = Array.from(d.querySelectorAll('input')).map((x) => x.value).filter(Boolean)
    const disabled = Array.from(d.querySelectorAll('.el-select.is-disabled')).length
    return { values: inputs.slice(0, 4), disabledSelects: disabled }
  })
  console.log('审核弹窗:', JSON.stringify(dlg))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'applications-review-locked.png') })
  await browser.close()
})()
