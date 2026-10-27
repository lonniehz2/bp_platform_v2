const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const BATCH = '373384637113831424'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('PAGEERROR', String(e).slice(0, 200)))
  page.on('request', (r) => {
    if (r.url().includes('/allocation/lottery') || r.url().includes('/allocation/batches')) {
      console.log('REQ', r.method(), r.url().replace(BASE, ''), (r.postData() || '').slice(0, 160))
    }
  })
  page.on('response', async (r) => {
    if (r.url().includes('/allocation/lottery')) {
      let b = ''
      try { b = JSON.stringify(await r.json()).slice(0, 200) } catch (e) { b = 'no-json' }
      console.log('RESP', r.status(), b)
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
  // 搜索该批次（用关键字? 无）—— 直接按行找 id 文本
  const clicked = await page.evaluate((batch) => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    const row = rows.find((r) => r.innerText.includes(batch))
    if (!row) return 'row-not-found'
    const b = Array.from(row.querySelectorAll('button')).find((x) => x.innerText.trim() === '摇号')
    if (!b) return 'button-not-found'
    b.click()
    return row.innerText.replace(/\s+/g, ' ').slice(0, 80)
  }, BATCH)
  console.log('点击行:', clicked)
  await sleep(1500)
  console.log('弹窗按钮:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).filter((b) => b.offsetParent)
      .map((x) => x.innerText.trim()).filter(Boolean).slice(-8))))
  console.log('弹窗文本:', await page.evaluate(() => {
    const box = document.querySelector('.el-message-box')
    return box ? box.innerText.replace(/\s+/g, ' ').slice(0, 120) : 'none'
  }))
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('.el-message-box button'))
    const b = btns.find((x) => x.innerText.includes('摇号')) || btns[btns.length - 1]
    if (b) b.click()
  })
  await sleep(4000)
  console.log('提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message')).map((x) => x.innerText.trim()))))
  await browser.close()
})()
