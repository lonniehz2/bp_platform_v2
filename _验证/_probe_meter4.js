const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  page.on('console', (m) => { if (m.type() === 'warning' || m.type() === 'error') console.log('CONSOLE', m.type(), m.text().slice(0,200)) })
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
  await page.evaluate(() => { location.hash = '#/meter-readings' })
  await sleep(3000)
  const info = await page.evaluate(() => ({
    hash: location.hash,
    head: document.body.innerText.slice(0, 200).replace(/\n/g, ' | '),
    tail: document.body.innerText.slice(-200).replace(/\n/g, ' | '),
    pagers: document.querySelectorAll('.el-pagination').length,
    tables: document.querySelectorAll('.el-table').length,
    rows: document.querySelectorAll('.el-table__body tr').length
  }))
  console.log(JSON.stringify(info, null, 1))
  await b.close()
})()
