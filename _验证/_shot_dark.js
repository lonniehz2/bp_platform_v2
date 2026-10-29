const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)

  // 浅色
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
  await page.evaluate(() => localStorage.setItem('bp.ui.mode', 'light'))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(900)
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
  await sleep(1800)
  await page.screenshot({ path: '_验证/theme_light_dashboard.png' })

  // 切深色（点按钮）
  const clicked = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('.header button, .el-header button'))
      .filter((b) => b.offsetParent && !b.innerText.trim())
    if (btns[0]) { btns[0].click(); return true }
    return false
  })
  await sleep(1200)
  const isDark = await page.evaluate(() => document.documentElement.classList.contains('dark'))
  console.log('toggle clicked:', clicked, 'dark:', isDark)
  await page.screenshot({ path: '_验证/theme_dark_dashboard.png' })

  // 表格页深色
  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(3000)
  await page.screenshot({ path: '_验证/theme_dark_houses.png' })

  // 弹窗深色
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('新增房源'))
    if (x) x.click()
  })
  await sleep(1000)
  await page.screenshot({ path: '_验证/theme_dark_dialog.png' })
  await b.close()
})()
