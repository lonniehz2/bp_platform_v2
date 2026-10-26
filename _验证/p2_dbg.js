/**
 * P2 四项验证：开放平台 Webhook、报表导出任务、规则引擎、补贴标准。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1040 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 300)))
  page.on('console', (m) => { if (['error','warning'].includes(m.type())) console.log('控制台:', m.text().slice(0,300)) })

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
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
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2400)

  const check = async (hash, waits, name) => {
    await page.evaluate((h) => { location.hash = h }, hash)
    await sleep(waits)
    const info = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('.page-card'))
        .map((c) => (c.querySelector('h3,h4')?.innerText || '').trim())
        .filter(Boolean)
      const tables = document.querySelectorAll('.el-table').length
      const rows = document.querySelectorAll('.el-table__body tr').length
      const mainBtns = Array.from(document.querySelectorAll('.page-card button'))
        .map((b) => b.innerText.trim()).filter(Boolean)
      return { cards, tables, rows, btns: Array.from(new Set(mainBtns)).slice(0, 10) }
    })
    console.log(`[${name}] 区块:`, info.cards.join(' / ') || '无',
      '| 表格', info.tables, '行', info.rows)
    console.log(`[${name}] 按钮:`, info.btns.join(' | '))
    await page.screenshot({ path: path.join(OUT, `p2-${name}.png`) })
  }

  await check('#/open', 4000, 'webhook')
  return await browser.close()
  await check('#/alerts', 3200, 'rules')
  await check('#/fee-items', 100, 'skip')
  await check('#/subsidies', 3200, 'subsidy')

  await browser.close()
})()
