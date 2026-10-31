const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  page.on('pageerror', (e) => console.log('PAGEERR', String(e).slice(0, 160)))
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
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
  await page.goto(BASE + '/#/contracts', { waitUntil: 'networkidle2' })
  await sleep(3000)
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建合同'))
    if (btn) btn.click()
  })
  await sleep(900)
  // 找到“承租人”表单项输入
  const clicked = await page.evaluate(() => {
    const item = Array.from(document.querySelectorAll('.el-dialog .el-form-item'))
      .find((x) => x.innerText.includes('承租人'))
    const inp = item && item.querySelector('input')
    if (inp) { inp.focus(); inp.click(); return true }
    return false
  })
  await page.keyboard.type('b66', { delay: 100 })
  await sleep(1800)
  await page.evaluate(() => {
    const o = Array.from(document.querySelectorAll('.el-select-dropdown__item'))
      .find((x) => x.innerText.includes('b66'))
    if (o) o.click()
  })
  await sleep(1800)
  console.log('autofill:', await page.evaluate(() => {
    const get = (label) => {
      const item = Array.from(document.querySelectorAll('.el-dialog .el-form-item'))
        .find((x) => x.innerText.includes(label))
      return item && item.querySelector('input')?.value
    }
    return { name: get('承租人姓名'), phone: get('联系电话'), org: get('出租组织') }
  }))
  await b.close()
})()
