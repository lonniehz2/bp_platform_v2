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
  page.on('dialog', async (d) => { console.log('对话框:', d.message().slice(0, 80)); await d.accept() })
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
  await page.evaluate(() => { location.hash = '#/allocations' })
  await sleep(3000)

  // 发布：点第一行的「发布」
  const before = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    const row = rows.find((r) => r.innerText.includes('发布'))
    if (!row) return null
    const btn = Array.from(row.querySelectorAll('button')).find((b) => b.innerText.trim() === '发布')
    if (btn) btn.click()
    return row.innerText.replace(/\s+/g, ' ').slice(0, 60)
  })
  console.log('点击发布行:', before)
  await sleep(1200)
  // 确认框
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-message-box button'))
      .find((x) => x.innerText.includes('确认'))
    if (b) b.click()
  })
  await sleep(2500)
  const msg = await page.evaluate(() => Array.from(document.querySelectorAll('.el-message'))
    .map((x) => x.innerText.trim()).slice(-2))
  console.log('发布提示:', JSON.stringify(msg))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'alloc-publish.png') })

  // 新建批次房源选项
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建批次'))
    if (b) b.click()
  })
  await sleep(2500)
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const item = Array.from(d.querySelectorAll('.el-form-item')).find((x) => x.innerText.includes('房源'))
    const w = item && item.querySelector('.el-select__wrapper')
    if (w) w.click()
  })
  await sleep(1500)
  const houseOpts = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-select-dropdown__item'))
      .map((x) => x.innerText.trim()).filter(Boolean))
  console.log('房源下拉项:', JSON.stringify(houseOpts))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'alloc-houses.png') })
  await browser.close()
})()
