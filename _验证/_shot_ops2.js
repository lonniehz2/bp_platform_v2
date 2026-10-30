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
  console.log('dark root:', await page.evaluate(() =>
    document.documentElement.classList.contains('dark')))
  await page.screenshot({ path: '_验证/ops_dark_forced.png' })

  // 强制改密
  const changed = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return false
    const ins = d.querySelectorAll('input')
    const set = (i, v) => { ins[i].focus(); ins[i].value = v
      ins[i].dispatchEvent(new Event('input', { bubbles: true }))
      ins[i].dispatchEvent(new Event('change', { bubbles: true })); ins[i].blur() }
    set(0, 'Ops@123456'); set(1, 'Ops@12345678'); set(2, 'Ops@12345678')
    const btn = Array.from(d.querySelectorAll('button')).find((x) => x.innerText.includes('保存'))
    if (btn) btn.click()
    return true
  })
  await sleep(1800)
  console.log('pwd changed:', changed)
  await page.screenshot({ path: '_验证/ops_dark_console.png' })
  await b.close()
})()
