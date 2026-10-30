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
  console.log('after set mode:', await page.evaluate(() => localStorage.getItem('bp.ui.mode')))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(1000)
  console.log('after reload:', await page.evaluate(() => ({
    mode: localStorage.getItem('bp.ui.mode'),
    dark: document.documentElement.classList.contains('dark'),
    bg: getComputedStyle(document.body).backgroundColor
  })))
  await page.screenshot({ path: '_验证/dark_check.png' })
  await b.close()
})()
