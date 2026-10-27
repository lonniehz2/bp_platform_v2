// 本轮 9 项界面验证
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
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))
  page.on('response', async (r) => {
    if (r.url().includes('/api/v1/orgs')) {
      try {
        const j = await r.json()
        console.log('ORG API', r.status(), Array.isArray(j.data) ? ('array ' + j.data.length) : ('keys=' + Object.keys(j.data || {}).join(',')))
      } catch (e) { console.log('ORG API parse fail', r.status()) }
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

  // 1) 房源台账：组织筛选
  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(3200)
  const house = await page.evaluate(() => {
    const sels = Array.from(document.querySelectorAll('.toolbar .el-select'))
    return { selects: sels.length,
      hasOrg: !!document.querySelector('[data-testid="house-org-filter"]') }
  })
  console.log('1) 房源筛选:', JSON.stringify(house))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'houses-org-filter.png') })

  // 2) 日房态：月份切换
  await page.evaluate(() => { location.hash = '#/house-calendar' })
  await sleep(3000)
  const cal = await page.evaluate(() => ({
    prev: !!document.querySelector('[data-testid="cal-month-prev"]'),
    month: !!document.querySelector('[data-testid="cal-month"]'),
    next: !!document.querySelector('[data-testid="cal-month-next"]')
  }))
  console.log('2) 日房态月份:', JSON.stringify(cal))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'calendar-month.png') })

  // 3) 申请受理：线下通过按钮
  await page.evaluate(() => { location.hash = '#/applications' })
  await sleep(3200)
  const app = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr')).slice(0, 3)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 90))
    const btns = Array.from(document.querySelectorAll('.el-table__body button'))
      .map((b) => b.innerText.trim())
    return { rows, btns: Array.from(new Set(btns)).slice(0, 8) }
  })
  console.log('3) 申请列表按钮:', app.btns.join(' / '))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'applications-offline.png') })

  // 4) 轮候：组织筛选 + 组织列
  await page.evaluate(() => { location.hash = '#/waitlist' })
  await sleep(3000)
  const wait = await page.evaluate(() => ({
    hasOrg: !!document.querySelector('[data-testid="wait-org"]'),
    headers: Array.from(document.querySelectorAll('.el-table__header th')).map((x) => x.innerText.trim())
  }))
  console.log('4) 轮候:', JSON.stringify(wait))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'waitlist-org.png') })

  // 5) 配租：组织筛选 + 新建批次
  await page.evaluate(() => { location.hash = '#/allocations' })
  await sleep(3200)
  const alloc = await page.evaluate(() => ({
    hasOrgFilter: !!document.querySelector('[data-testid="alloc-org"]'),
    headers: Array.from(document.querySelectorAll('.el-table__header th')).map((x) => x.innerText.trim()).slice(0, 8)
  }))
  console.log('5) 配租:', JSON.stringify(alloc))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建批次'))
    if (b) b.click()
  })
  await sleep(1800)
  const dlg = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return { labels: Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim()),
      values: Array.from(d.querySelectorAll('input')).map((x) => x.value).filter(Boolean).slice(0, 3) }
  })
  console.log('6) 新建批次弹窗:', JSON.stringify(dlg))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'alloc-create.png') })

  await browser.close()
})()
