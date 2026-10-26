// IoT 参数：页面保存 → 接口回读
const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1200 })
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
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2200)
  await page.evaluate(() => { location.hash = '#/sys/config' })
  await sleep(3600)

  // 找到「指令超时」行的输入框，改成 12，点保存
  const done = await page.evaluate(() => {
    const card = Array.from(document.querySelectorAll('.el-card'))
      .find((c) => (c.innerText || '').includes('IoT 对接参数'))
    if (!card) return 'no card'
    const rows = Array.from(card.querySelectorAll('.el-table__body tr'))
    const target = rows.find((tr) => tr.innerText.includes('指令超时'))
    if (!target) return 'no row'
    const input = target.querySelector('input')
    if (!input) return 'no input'
    input.focus(); input.value = '12'
    input.dispatchEvent(new Event('input', { bubbles: true }))
    input.dispatchEvent(new Event('change', { bubbles: true }))
    input.blur()
    const btn = Array.from(target.querySelectorAll('button')).find((b) => b.innerText.includes('保存'))
    if (btn) btn.click()
    return 'clicked'
  })
  console.log('操作:', done)
  await sleep(1800)
  await page.screenshot({ path: path.join(__dirname, '_shots', 'iot-settings-saved.png') })
  await browser.close()
})()
