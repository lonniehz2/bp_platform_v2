const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('PAGEERROR', String(e).slice(0, 160)))
  page.on('request', (r) => {
    if (r.url().includes('/allocation/') && r.method() === 'POST') {
      console.log('POST', r.url().replace(BASE, ''), (r.postData() || '').slice(0, 120))
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
  await sleep(3200)

  // 加房源：第一行点「加房源」
  await page.evaluate(() => {
    const row = Array.from(document.querySelectorAll('.el-table__body tr'))[0]
    const b = row && Array.from(row.querySelectorAll('button')).find((x) => x.innerText.trim() === '加房源')
    if (b) b.click()
  })
  await sleep(1500)
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const ta = d && d.querySelector('textarea')
    if (ta) { ta.focus(); ta.value = '371004675903852544'
      ta.dispatchEvent(new Event('input', { bubbles: true })) }
  })
  await sleep(400)
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const b = d && Array.from(d.querySelectorAll('button')).find((x) => x.innerText.trim() === '加入')
    if (b) b.click()
  })
  await sleep(2500)
  console.log('加房源提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message')).map((x) => x.innerText.trim()))))

  // 生成配租单：找 LOTTERY_DONE 行
  const gen = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    for (const r of rows) {
      const b = Array.from(r.querySelectorAll('button')).find((x) => x.innerText.trim() === '生成配租单')
      if (b) { b.click(); return r.innerText.replace(/\s+/g, ' ').slice(0, 60) }
    }
    return null
  })
  console.log('生成配租单行:', gen)
  await sleep(1200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-message-box button')).find((x) => x.innerText.includes('确认'))
    if (b) b.click()
  })
  await sleep(2500)
  console.log('生成提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message')).map((x) => x.innerText.trim()))))
  await browser.close()
})()
