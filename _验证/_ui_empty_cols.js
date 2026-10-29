const puppeteer = require('puppeteer-core')
const fs = require('fs')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const ROUTES = ['#/applications', '#/allocations', '#/contracts', '#/contract-changes', '#/meter-readings',
  '#/bills', '#/devices', '#/houses', '#/persons', '#/terminations', '#/exchanges', '#/complaints',
  '#/visits', '#/short-rent', '#/workorders', '#/alerts', '#/subsidies', '#/deposits',
  '#/publicities', '#/waitlist', '#/fee-items', '#/arrears', '#/cashflow', '#/annual-reviews',
  '#/spaces', '#/orgs', '#/energy', '#/reports', '#/gov', '#/access', '#/keyring', '#/grants',
  '#/credits', '#/appeals', '#/messages', '#/todos', '#/open', '#/ops-center']
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
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
  const out = []
  for (const r of ROUTES) {
    await page.evaluate((x) => { location.hash = x }, r)
    await sleep(2400)
    const cols = await page.evaluate(() => {
      const t = document.querySelector('.el-table')
      if (!t) return []
      const heads = Array.from(t.querySelectorAll('.el-table__header th')).map((h) => h.innerText.trim())
      const body = Array.from(t.querySelectorAll('.el-table__body tr')).slice(0, 30)
      return heads.map((h, i) => {
        if (!h || ['操作', ''].includes(h)) return null
        const vals = body.map((tr) => (tr.children[i] ? tr.children[i].innerText.trim() : ''))
        const empty = vals.filter((v) => !v || v === '—').length
        return { h, ratio: vals.length ? empty / vals.length : 0, n: vals.length }
      }).filter(Boolean)
    })
    const weak = cols.filter((c) => c.n >= 3 && c.ratio >= 0.8)
    if (weak.length) out.push({ route: r, weak })
  }
  fs.writeFileSync(__dirname + '/_ui_empty_cols.json', JSON.stringify(out, null, 2), 'utf8')
  console.log(out.map((o) => o.route + ' -> ' + o.weak.map((w) => w.h + '(' + Math.round(w.ratio * 100) + '%)').join(', ')).join('\n'))
  await browser.close()
})()
