const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  const bad = []
  page.on('response', async (res) => {
    const u = res.url()
    if (u.includes('/api/') && res.status() >= 400) {
      let body = ''
      try { body = (await res.text()).slice(0, 160) } catch (e) {}
      bad.push(res.status() + ' ' + u.replace(BASE, '') + ' ' + body)
    }
  })
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2000)
  await page.evaluate(() => { location.hash = '#/publicities' })
  await sleep(4000)
  console.log('错误响应:', JSON.stringify(bad, null, 1))
  console.log('页面提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message, .el-alert__title')).map((x) => x.innerText.trim()).slice(0, 3))))
  console.log('表格行:', await page.evaluate(() => document.querySelectorAll('.el-table__body tr').length))
  await browser.close()
})()
