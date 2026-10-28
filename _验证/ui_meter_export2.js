const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1600, height: 1000 })
  await page.setCacheEnabled(false)
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
    if (b) b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)
  await page.evaluate(() => { location.hash = '#/meter-readings' })
  await sleep(3500)
  const buttons = await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean))
  console.log('按钮:', JSON.stringify(buttons.filter(t => t.includes('录入') || t.includes('批量'))))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('批量录入'))
    if (b) b.click()
  })
  await sleep(1200)
  const batch = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    if (!d) return null
    return { text: d.innerText.slice(0, 60).replace(/\n/g, ' | '),
      heads: Array.from(d.querySelectorAll('th')).map(t => t.innerText.trim()).filter(Boolean) }
  })
  console.log('批量弹窗:', JSON.stringify(batch))
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    const b = d && Array.from(d.querySelectorAll('button')).find(x => x.innerText.includes('导出 CSV'))
    if (b) b.click()
  })
  await sleep(900)
  const exp = await page.evaluate(() => {
    const downs = Array.from(document.querySelectorAll('.el-dialog')).filter(x => x.offsetParent)
    const d = downs[downs.length - 1]
    return d ? d.innerText.slice(0, 80).replace(/\n/g, ' | ') : null
  })
  console.log('导出弹窗:', JSON.stringify(exp))
  await browser.close()
})()
