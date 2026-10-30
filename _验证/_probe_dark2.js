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
  await sleep(800)
  await page.evaluate(() => localStorage.setItem('bp.ui.mode', 'dark'))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(700)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(300)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('登'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)
  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(2500)
  console.log(JSON.stringify(await page.evaluate(() => {
    const card = document.querySelector('.page-card')
    const th = document.querySelector('.el-table th')
    const table = document.querySelector('.el-table')
    const cs = (e) => e ? getComputedStyle(e) : null
    return {
      dark: document.documentElement.classList.contains('dark'),
      cardClass: card?.className,
      cardVar: cs(card)?.getPropertyValue('--bp-card-bg'),
      cardBg: cs(card)?.backgroundColor,
      cardInline: card?.getAttribute('style'),
      tableBg: cs(table)?.backgroundColor,
      thBg: cs(th)?.backgroundColor,
      thClass: th?.className,
      parentBg: cs(card?.parentElement)?.backgroundColor,
      styles: Array.from(document.styleSheets).map((s) => s.href || 'inline').slice(0, 20)
    }
  }), null, 1))
  await b.close()
})()
