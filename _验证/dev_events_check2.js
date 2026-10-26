/**
 * 设备告警页验证：统计口径 + 详情中文 + 类型说明。
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
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 150)))

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

  await page.evaluate(() => { location.hash = '#/dev-events' })
  await sleep(3200)

  const info = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.el-card'))
      .map((c) => c.innerText.replace(/\s+/g, ' ').trim())
    const rows = Array.from(document.querySelectorAll('.el-table__body tr')).slice(0, 4)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 160))
    return { cards: cards.slice(0, 4), rows,
      total: document.querySelector('.el-pagination__total')?.innerText }
  })
  console.log('统计卡片:', info.cards.join(' | '))
  console.log('分页:', info.total)
  info.rows.slice(0, 3).forEach((r, i) => console.log('行' + (i + 1) + ':', r))
  await page.screenshot({ path: path.join(OUT, 'dev-events-fixed.png') })

  await browser.close()
})()
