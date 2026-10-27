const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('页面异常:', String(e).slice(0, 200)))
  page.on('response', async (r) => {
    const u = r.url()
    if (/\/api\/v1\/(applications\/\d+\/accept|allocation\/batches)/.test(u)) {
      let body = ''
      try { body = JSON.stringify(await r.json()).slice(0, 120) } catch (e) { body = 'no-json' }
      console.log('API', r.request().method(), u.replace(BASE, ''), r.status(), body)
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

  // 1) 受理
  await page.evaluate(() => { location.hash = '#/applications' })
  await sleep(3200)
  await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input')).find((x) => x.placeholder && x.placeholder.includes('姓名'))
    if (inp) { inp.focus(); inp.value = 'BA373365531077644288'
      inp.dispatchEvent(new Event('input', { bubbles: true })) }
  })
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '查询')
    if (b) b.click()
  })
  await sleep(1800)
  const clicked = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    for (const r of rows) {
      const btn = Array.from(r.querySelectorAll('button')).find((b) => b.innerText.trim() === '受理')
      if (btn) { btn.click(); return r.innerText.replace(/\s+/g, ' ').slice(0, 50) }
    }
    return null
  })
  console.log('受理点击行:', clicked)
  await sleep(2500)
  console.log('受理提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message')).map((x) => x.innerText.trim()))))

  // 2) 新建批次
  await page.evaluate(() => { location.hash = '#/allocations' })
  await sleep(3200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建批次'))
    if (b) b.click()
  })
  await sleep(2200)
  const filled = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return false
    const inputs = Array.from(d.querySelectorAll('input'))
    const name = inputs[0]
    name.focus(); name.value = 'UI验证批次' + Date.now() % 100000
    name.dispatchEvent(new Event('input', { bubbles: true }))
    return { name: name.value, org: (d.querySelector('.el-select input') || {}).value }
  })
  console.log('批次表单:', JSON.stringify(filled))
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const b = Array.from(d.querySelectorAll('button')).find((x) => x.innerText.includes('创建'))
    if (b) b.click()
  })
  await sleep(2500)
  console.log('创建提示:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-message')).map((x) => x.innerText.trim()))))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'alloc-create-result.png') })

  // 3) 参与人数列
  const headers = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table__header th')).map((x) => x.innerText.trim()))
  console.log('批次表头:', JSON.stringify(headers.slice(0, 9)))
  await browser.close()
})()
