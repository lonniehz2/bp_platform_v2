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
  await sleep(1500)
  for (const r of ['#/meter-readings']) {
    await page.evaluate((x) => { location.hash = x }, r)
    await sleep(2600)
    const info = await page.evaluate(() => {
      const p = document.querySelector('.el-pagination'); const all=document.body.innerText.includes('共')
      if (!p) return { pager: false }
      const sel = p.querySelector('.el-select')
      const rows = document.querySelectorAll('.el-table__body tr').length
      return { pager: true, bodyTotal: all, sizes: !!sel, total: (p.querySelector('.el-pagination__total') || {}).innerText,
        rows }
    })
    console.log(r, JSON.stringify(info))
  }
  await b.close()
})()
