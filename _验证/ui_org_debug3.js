const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setCacheEnabled(false)
  page.on('console', (m) => console.log('CONSOLE', m.type(), m.text().slice(0, 200)))
  page.on('requestfailed', (r) => console.log('REQ FAIL', r.url(), r.failure() && r.failure().errorText))
  page.on('response', async (r) => {
    if (r.url().includes('/api/v1/orgs')) {
      let body = ''
      try { body = JSON.stringify(await r.json()).slice(0, 160) } catch (e) { body = 'parse-fail' }
      console.log('ORG RESP', r.status(), body)
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
  await page.evaluate(() => { location.hash = '#/allocations' })
  await sleep(2500)
  console.log('--- 打开新建批次 ---')
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建批次'))
    if (b) b.click()
  })
  await sleep(3000)
  // 在页面上下文直接 fetch 一次
  const direct = await page.evaluate(async () => {
    const token = localStorage.getItem('bp_token') || localStorage.getItem('token') || ''
    const tenant = localStorage.getItem('bp_tenant') || '350600'
    const r = await fetch('/api/v1/orgs?pageNum=1&pageSize=5', { headers: { Authorization: 'Bearer ' + token, 'X-Tenant-Id': tenant } })
    const j = await r.json()
    return { status: r.status, code: j.code, rows: (j.data && j.data.rows || []).length }
  })
  console.log('页面内 direct fetch:', JSON.stringify(direct))
  const chunk = await page.evaluate(async () => {
    const url = Array.from(performance.getEntriesByType('resource'))
      .map((e) => e.name).find((n) => n.includes('Allocations'))
    if (!url) return null
    const r = await fetch(url)
    const t = await r.text()
    return { url, len: t.length, hasNew: t.includes('选择组织后搜索待分配房源'),
      hasOld: t.includes('多个用逗号分隔') }
  })
  console.log('Allocations chunk:', JSON.stringify(chunk))
  const idx = await page.evaluate(async () => {
    const r = await fetch('/index.html?x=' + Date.now())
    const t = await r.text()
    const m = t.match(/assets\/index-[^"]+\.js/)
    return m ? m[0] : null
  })
  console.log('index entry:', idx)
  await browser.close()
})()
