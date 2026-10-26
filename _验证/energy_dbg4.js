/**
 * 数据重建后的关键页面截图：驾驶舱 / 账单 / 催缴 / 能耗。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const PAGES = [['#/energy', 'energy']]

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 200)))
  page.on('response', (r) => { if (r.status() >= 400) console.log('HTTP', r.status(), r.url().slice(-60)) })
  page.on('console', (m) => { if (m.type()==='error') console.log('控制台:', m.text().slice(0,180)) })

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForSelector('.el-table__body tr, .stat-card', { timeout: 30000 })

  for (const [hash, name] of PAGES) {
    await page.evaluate((h) => { location.hash = h }, hash)
    await sleep(3200)
    const probe = await page.evaluate(async () => {
      const t = localStorage.getItem('bp_token') || ''
      const r = await fetch('/api/v1/fin/meter-readings/analytics?months=6', { headers: { Authorization: 'Bearer ' + t, 'X-Tenant-Id': '350600' } })
      const j = await r.json()
      return { status: r.status, months: (j.data && j.data.months || []).length }
    })
    console.log('页面内直接请求:', JSON.stringify(probe))
    const summary = await page.evaluate(() => {
      const sc = Array.from(document.querySelectorAll('.stat-card'))
        .map((x) => x.innerText.replace(/\n+/g, ' ').slice(0, 40))
      const tr = document.querySelector('.el-table__body tr')
      return {
        cards: sc.slice(0, 4),
        row: tr ? tr.innerText.replace(/\n+/g, ' | ').slice(0, 120) : '无表格行',
        svgs: document.querySelectorAll('svg').length
      }
    })
    await page.screenshot({ path: path.join(OUT, 'seed-' + name + '.png') })
    console.log(name, '| 卡片:', summary.cards.join(' / ') || '-', '| 行:', summary.row)
  }
  await browser.close()
})()
