const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
  await page.setCacheEnabled(false)
  page.on('console', (m) => console.log('CONSOLE', m.type(), m.text().slice(0, 160)))
  page.on('pageerror', (e) => console.log('PAGEERROR', String(e).slice(0, 200)))
  page.on('request', (r) => {
    if (r.url().includes('/allocation/batches') && r.method() === 'POST') {
      console.log('POST', r.url().replace(BASE, ''), JSON.stringify(r.postData()).slice(0, 200))
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
  await sleep(2200)
  await page.evaluate(() => { location.hash = '#/allocations' })
  await sleep(3200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建批次'))
    if (b) b.click()
  })
  await sleep(2500)
  const dialogInfo = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return {
      buttons: Array.from(d.querySelectorAll('button')).map((b) => b.innerText.trim()),
      inputs: Array.from(d.querySelectorAll('input')).map((i) => ({ ph: i.placeholder, val: i.value }))
    }
  })
  console.log('弹窗:', JSON.stringify(dialogInfo))
  // 用键盘输入批次名称
  const handle = await page.evaluateHandle(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return d.querySelectorAll('input')[0]
  })
  await handle.asElement().click()
  await page.keyboard.type('UI创建' + (Date.now() % 100000))
  await sleep(500)
  const val = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return Array.from(d.querySelectorAll('input')).map((i) => i.value).slice(0, 3)
  })
  console.log('输入值:', JSON.stringify(val))
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const b = Array.from(d.querySelectorAll('button')).find((x) => x.innerText.trim() === '创建')
    if (b) { b.focus(); b.click() }
  })
  await sleep(3000)
  console.log('提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message')).map((x) => x.innerText.trim()))))
  await browser.close()
})()
