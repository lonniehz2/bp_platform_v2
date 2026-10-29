const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1440, height: 900 })
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
  await sleep(1600)
  await page.evaluate(() => { location.hash = '#/bills' })
  await sleep(4000)
  console.log('buttons:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).map((x) => x.innerText.trim())
      .filter((t) => ['批量出账', '批量催缴', '重算历史账单'].includes(t)))))
  console.log('heads:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table__header th')).map((t) => t.innerText.trim()))))
  console.log('first row:', JSON.stringify(await page.evaluate(() => {
    const tr = document.querySelector('.el-table__body tr')
    return tr ? Array.from(tr.children).slice(0, 7).map((td) => td.innerText.trim()) : null
  })))
  await b.close()
})()
