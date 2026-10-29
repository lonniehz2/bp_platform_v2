const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
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

  const lr = await fetch(BASE + '/api/v1/auth/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Tenant-Id': '350600' },
    body: JSON.stringify({ tenantCode: '350600', username: 'admin', password: 'admin123' })
  })
  const token = (await lr.json()).data.token
  const api = async (p) => {
    const r = await fetch(BASE + '/api/v1' + p,
      { headers: { 'X-Tenant-Id': '350600', Authorization: 'Bearer ' + token } })
    return (await r.json()).data
  }
  const cases = [
    ['#/houses', '/houses?pageNum=1&pageSize=1', (r) => r.houseCode, '房源编号'],
    ['#/persons', '/persons?pageNum=1&pageSize=1', (r) => r.personName, '姓名'],
    ['#/contracts', '/contracts?pageNum=1&pageSize=1', (r) => r.contractNo, '合同号'],
    ['#/bills', '/fin/bills?pageNum=1&pageSize=1', (r) => r.billNo, '账单号'],
    ['#/devices', '/devices?pageNum=1&pageSize=1', (r) => r.deviceId, '设备编号']
  ]
  for (const [route, apiPath, pick, label] of cases) {
    let sample = ''
    try {
      const d = await api(apiPath)
      sample = String(pick(d.rows[0]))
    } catch (e) { sample = '' }
    await page.evaluate((r) => { location.hash = r }, route)
    await sleep(2600)
    const before = await page.evaluate(() => document.querySelectorAll('.el-table__body tr').length)
    const typed = await page.evaluate((v) => {
      const tb = document.querySelector('.toolbar') || document.body
      const inp = Array.from(tb.querySelectorAll('input'))
        .find((i) => i.type === 'text' && i.offsetParent)
      if (!inp) return false
      inp.focus(); inp.value = v
      inp.dispatchEvent(new Event('input', { bubbles: true }))
      inp.dispatchEvent(new Event('change', { bubbles: true }))
      inp.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', bubbles: true }))
      inp.blur()
      return true
    }, sample)
    await sleep(700)
    await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '查询')
      if (b) b.click()
    })
    await sleep(1800)
    const after = await page.evaluate((v) => {
      const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
      return { n: rows.length, hit: rows.slice(0, 5).every((r) => r.innerText.includes(v)) }
    }, sample)
    console.log(`${route}\t${label}=${sample}\t行 ${before}→${after.n}\t命中=${after.hit}`)
  }
  await browser.close()
})()
