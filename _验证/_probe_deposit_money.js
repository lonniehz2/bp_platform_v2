const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
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
  await page.evaluate(() => { location.hash = '#/deposits' })
  await sleep(3500)
  // 从列表取一个合同号显示? 直接调用接口拿合同ID
  const cid = await page.evaluate(async () => {
    const r = await fetch('/api/v1/contracts?pageNum=1&pageSize=1&status=EFFECTIVE', {
      headers: { 'X-Tenant-Id': '350600', 'Authorization': 'Bearer ' + (window.__TOKEN || '') }
    }).catch(() => null)
    return null
  })
  // 打开押金建档
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('押金建档'))
    if (b) b.click()
  })
  await sleep(1000)
  const info = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    if (!d) return null
    return { inputs: Array.from(d.querySelectorAll('input')).map(i => ({ ph: i.placeholder, v: i.value })),
      text: d.innerText.slice(0, 80).replace(/\n/g, ' | ') }
  })
  console.log('押金表格:', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.el-table__body tr')).slice(0,3).map(r=>r.innerText.slice(0,80).replace(/\n/g,' | ')))))
  console.log('押金弹窗:', JSON.stringify(info))
  await browser.close()
})()
