/**
 * 采集页面加载中的 404 / 失败请求，定位缺失资源。
 */
const puppeteer = require('puppeteer-core')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  const failed = []
  page.on('response', (r) => {
    if (r.status() >= 400) failed.push(r.status() + ' ' + r.url())
  })
  page.on('requestfailed', (r) => failed.push('FAILED ' + r.url()))

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
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
  await new Promise(r => setTimeout(r, 300))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(
    () => !!document.querySelector('.rail, .el-menu, .aside'), { timeout: 20000 })
  await page.goto(BASE + '/#/dashboard', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))

  console.log('失败请求数:', failed.length)
  for (const f of [...new Set(failed)].slice(0, 15)) console.log('  ' + f)
  await browser.close()
})()
