const puppeteer = require('puppeteer-core')
const fs = require('fs')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const ROUTES = ['#/applications', '#/allocations', '#/contracts', '#/contract-changes', '#/meter-readings',
  '#/bills', '#/devices', '#/houses', '#/persons', '#/terminations', '#/exchanges', '#/complaints',
  '#/visits', '#/short-rent', '#/workorders', '#/alerts', '#/subsidies', '#/deposits',
  '#/publicities', '#/waitlist', '#/fee-items', '#/arrears', '#/cashflow', '#/annual-reviews',
  '#/spaces', '#/orgs', '#/applications', '#/energy']
const RE = /^(新建|新增|录入|导出|导入|批量|发起|登记|分配|创建)/
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  let jsErr = []
  page.on('pageerror', (e) => jsErr.push(String(e).slice(0, 120)))
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
  for (const route of ROUTES) {
    jsErr = []
    await page.evaluate((r) => { location.hash = r }, route)
    await sleep(2500)
    const names = await page.evaluate((re) => {
      const rx = new RegExp(re)
      return Array.from(document.querySelectorAll('.toolbar button, .page-head button, button'))
        .map((b) => b.innerText.trim()).filter((t) => rx.test(t)).slice(0, 2)
    }, RE.source)
    for (const name of names) {
      const clicked = await page.evaluate((n) => {
        const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === n)
        if (b) { b.click(); return true }
        return false
      }, name)
      if (!clicked) continue
      await sleep(1200)
      const info = await page.evaluate(() => {
        const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
        if (!d) return { open: false }
        return { open: true,
          inputs: d.querySelectorAll('input').length,
          selects: d.querySelectorAll('.el-select').length,
          text: d.innerText.slice(0, 40).replace(/\n/g, ' ') }
      })
      out.push({ route, name, ...info, js: jsErr.slice(0, 2) })
      await page.keyboard.press('Escape')
      await sleep(500)
    }
  }
  fs.writeFileSync(__dirname + '/_ui_dialog_audit.json', JSON.stringify(out, null, 2), 'utf8')
  console.log(out.map((o) => `${o.route}\t${o.name}\t${o.open ? '打开' : '未打开'}\t输入${o.inputs ?? 0}/选择${o.selects ?? 0}\t${o.js?.length ? 'JS错' : ''}`).join('\n'))
  await browser.close()
})()
