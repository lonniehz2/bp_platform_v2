const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const BATCH = '373398249891041280'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('PAGEERROR', String(e).slice(0, 160)))
  page.on('response', async (r) => {
    if (r.url().includes('/allocation/') && r.request().method() === 'POST') {
      let b = ''
      try { b = JSON.stringify(await r.json()).slice(0, 120) } catch (e) { b = '' }
      console.log('RESP', r.url().replace(BASE, ''), r.status(), b)
    }
  })
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
  await page.evaluate(() => { location.hash = '#/allocations' })
  await sleep(3500)

  console.log('表头:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table__header th')).map((x) => x.innerText.trim()).slice(0, 9))))

  // 摇号
  const click = await page.evaluate((batch) => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    const row = rows.find((r) => r.innerText.includes(batch))
    if (!row) return 'row-not-found'
    const b = Array.from(row.querySelectorAll('button')).find((x) => x.innerText.trim() === '摇号')
    if (!b) return 'no-lottery-button'
    b.click()
    return 'clicked'
  }, BATCH)
  console.log('摇号点击:', click)
  await sleep(1500)
  // 确认对话框：找可见的确定/开始摇号
  const boxText = await page.evaluate(() => {
    const box = document.querySelector('.el-message-box')
    return box ? box.innerText.replace(/\s+/g, ' ').slice(0, 100) : 'none'
  })
  console.log('确认框:', boxText)
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('.el-message-box button'))
    const b = btns.find((x) => /摇号|确定|确认/.test(x.innerText))
    if (b) b.click()
  })
  await sleep(4000)
  console.log('提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message')).map((x) => x.innerText.trim()))))

  // 加房源弹窗
  await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    const row = rows.find((r) => Array.from(r.querySelectorAll('button')).some((b) => b.innerText.trim() === '加房源'))
    const b = row && Array.from(row.querySelectorAll('button')).find((x) => x.innerText.trim() === '加房源')
    if (b) b.click()
  })
  await sleep(2500)
  const dialog = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return { title: d.querySelector('.el-dialog__title')?.innerText,
      sections: Array.from(d.querySelectorAll('h4')).map((x) => x.innerText.trim()),
      rows: d.querySelectorAll('.el-table__body tr').length }
  })
  console.log('加房源弹窗:', JSON.stringify(dialog))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'alloc-house-dialog.png') })
  await browser.close()
})()
