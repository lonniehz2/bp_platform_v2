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
  await page.evaluate(() => localStorage.removeItem('bp.ui.mode'))
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
  console.log('initial:', await page.evaluate(() => document.documentElement.classList.contains('dark')))
  // 点月亮按钮
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('.el-header button'))
      .find((x) => x.className.includes('is-circle'))
    if (btn) btn.click()
  })
  await sleep(800)
  console.log('after toggle:', await page.evaluate(() => ({
    dark: document.documentElement.classList.contains('dark'),
    mode: localStorage.getItem('bp.ui.mode')
  })))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(2000)
  console.log('after reload:', await page.evaluate(() => ({
    dark: document.documentElement.classList.contains('dark'),
    mode: localStorage.getItem('bp.ui.mode')
  })))
  await page.screenshot({ path: '_验证/dark_persist.png' })
  await b.close()
})()
