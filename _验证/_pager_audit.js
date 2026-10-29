const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const ROUTES = [
  '#/dashboard', '#/applications', '#/allocations', '#/contracts', '#/contract-changes',
  '#/meter-readings', '#/energy', '#/bills', '#/reports', '#/devices', '#/device-bind',
  '#/dev-events', '#/iot-reconcile', '#/iot-monitor', '#/iot-tools', '#/dev-commands',
  '#/access', '#/orgs', '#/houses', '#/todos', '#/messages', '#/workorders', '#/alerts',
  '#/keyring', '#/grants', '#/persons', '#/spaces', '#/terminations', '#/appeals',
  '#/credits', '#/exchanges', '#/complaints', '#/visits', '#/short-rent',
  '#/house-calendar', '#/gov', '#/open', '#/rbac', '#/sys', '#/subsidies',
  '#/deposits', '#/publicities', '#/waitlist', '#/fee-items', '#/arrears',
  '#/cashflow', '#/annual-reviews', '#/ops-center', '#/help'
]

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  let errors = []
  let badApi = []
  let pageErrors = []
  page.on('pageerror', (e) => pageErrors.push(String(e).slice(0, 160)))
  page.on('response', async (res) => {
    if (res.url().includes('/api/') && res.status() >= 400) {
      let body = ''
      try { body = (await res.text()).slice(0, 120) } catch (e) {}
      badApi.push(res.status() + ' ' + res.url().replace(BASE, '') + ' ' + body)
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
    if (b) b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1800)

  const results = []
  for (const route of ROUTES) {
    errors = []
    badApi = []
    pageErrors = []
    await page.evaluate((r) => { location.hash = r }, route)
    await sleep(2600)
    const info = await page.evaluate(() => ({pager: document.querySelectorAll('.el-pagination').length, rows: document.querySelectorAll('.el-table__body tr').length}));
    const unused = await page.evaluate(() => {
      const text = document.body.innerText
      const bad = ['系统异常', 'undefined', 'NaN', '[object Object]', '资源不存在']
        .filter((k) => text.includes(k))
      const tables = document.querySelectorAll('.el-table')
      let rows = 0
      tables.forEach((t) => { rows += t.querySelectorAll('.el-table__body tr').length })
      const empty = document.querySelectorAll('.el-table__empty-text').length
      const overflow = document.documentElement.scrollWidth
        - document.documentElement.clientWidth
      const wide = Array.from(document.querySelectorAll('body *'))
        .filter((el) => el.scrollWidth > el.clientWidth + 40
          && ['DIV', 'TABLE'].includes(el.tagName))
        .length
      return { bad, rows, tables: tables.length, empty, overflow, wide,
        h3: (document.querySelector('h3') || {}).innerText || '' }
    })
    results.push({ route, pager: info.pager, rows: info.rows })
  }

  const noPager = results.filter(r => r.rows > 0 && r.pager === 0).map(r => r.route);
  console.log('有数据但无分页:', JSON.stringify(noPager));
  const report = results.map((r) => {
    const flags = []
    if (r.bad.length) flags.push('文案异常:' + r.bad.join('/'))
    if (r.api.length) flags.push('接口错:' + r.api.length)
    if (r.js.length) flags.push('JS错:' + r.js.length)
    if (r.overflow > 20) flags.push('横向溢出:' + r.overflow + 'px')
    if (r.tables === 0) flags.push('无表格')
    if (r.rows === 0 && r.empty === 0 && r.tables > 0) flags.push('表格空且无提示')
    return { route: r.route, title: r.h3.slice(0, 16), rows: r.rows, flags }
  })
  fs.writeFileSync(path.join(__dirname, '_ui_audit.json'),
    JSON.stringify({ results, report }, null, 2), 'utf8')
  const lines = report.map((x) => `${x.route}\t${x.title}\t行=${x.rows}\t${x.flags.join('；') || 'OK'}`)
  console.log(lines.join('\n'))
  await browser.close()
})()
