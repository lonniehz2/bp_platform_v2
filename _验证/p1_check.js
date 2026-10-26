/**
 * P1 第一批验证：投诉处理/评价/转工单、公示发布、轮候退出、走访转工单、年审调租按钮。
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
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 170)))

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
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2400)

  const pages = [
    ['#/complaints', '投诉管理'],
    ['#/publicities', '公示管理'],
    ['#/waitlist', '轮候管理'],
    ['#/visits', '入户走访'],
    ['#/annual-reviews', '年审复核']
  ]
  for (const [hash, label] of pages) {
    await page.evaluate((h) => { location.hash = h }, hash)
    await sleep(2500)
    const info = await page.evaluate(() => {
      const row = document.querySelector('.el-table__body tr')
      return {
        title: document.querySelector('.page-card h3')?.innerText.trim(),
        btns: row ? Array.from(row.querySelectorAll('button'))
          .map((b) => b.innerText.trim()).filter(Boolean) : []
      }
    })
    console.log(`${label}: ${info.title} | ${info.btns.join(' / ') || '无操作列'}`)
    await page.screenshot({ path: path.join(OUT, `p1-${label}.png`) })
  }

  await browser.close()
})()
