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
  await sleep(800)
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
  await sleep(3000)
  console.log(JSON.stringify(await page.evaluate(() => {
    const t = document.querySelector('.el-table')
    const th = document.querySelector('.el-table th')
    const td = document.querySelector('.el-table__body td')
    const card = document.querySelector('.page-card')
    const cs = (el) => el ? getComputedStyle(el) : null
    return {
      dark: document.documentElement.classList.contains('dark'),
      cardBg: cs(card)?.backgroundColor,
      tableBg: cs(t)?.backgroundColor,
      thBg: cs(th)?.backgroundColor,
      thColor: cs(th)?.color,
      tdBg: cs(td)?.backgroundColor,
      tdColor: cs(td)?.color,
      tableVar: cs(document.documentElement).getPropertyValue('--el-table-bg-color'),
      headerVar: cs(document.documentElement).getPropertyValue('--el-table-header-bg-color'),
      htmlBg: cs(document.body)?.backgroundColor
    }
  }), null, 1))
  await b.close()
})()
