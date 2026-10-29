const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  await page.goto(BASE + '/#/platform-admin/login', { waitUntil: 'networkidle2' })
  await sleep(1200)
  await page.screenshot({ path: '_验证/ops_login.png' })

  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, 'opsadmin'); set(1, 'Ops@123456')
  })
  await sleep(300)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('登'))
    if (x) x.click()
  })
  await sleep(2500)
  console.log('hash:', await page.evaluate(() => location.hash))
  console.log('rows:', await page.evaluate(() => document.querySelectorAll('.el-table__body tr').length))
  await page.screenshot({ path: '_验证/ops_console.png' })

  // 打开详情
  const opened = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '详情')
    if (btn) { btn.click(); return true }
    return false
  })
  await sleep(1500)
  console.log('detail opened:', opened)
  await page.screenshot({ path: '_验证/ops_detail.png' })
  await b.close()
})()
