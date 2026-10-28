const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1600, height: 1000 })
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
  await sleep(1500)

  // 1) 合同：组织下拉选项
  await page.evaluate(() => { location.hash = '#/contracts' })
  await sleep(5000)
  const orgInfo = await page.evaluate(async () => {
    const el = document.querySelector('[data-testid="contract-org-filter"]')
    if (!el) return { found: false }
    el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
    el.click()
    await new Promise(r => setTimeout(r, 800))
    return { found: true, items: document.querySelectorAll('.el-select-dropdown__item').length,
      first: Array.from(document.querySelectorAll('.el-select-dropdown__item')).slice(0,2).map(x=>x.innerText.trim()) }
  })
  console.log('合同组织下拉:', JSON.stringify(orgInfo))
  await page.keyboard.press('Escape')

  // 2) 合同变更详情
  await page.evaluate(() => { location.hash = '#/contract-changes' })
  await sleep(4000)
  const chg = await page.evaluate(async () => {
    const rows = document.querySelectorAll('.el-table__body tr')
    if (!rows.length) return { rows: 0 }
    const btn = Array.from(rows[0].querySelectorAll('button')).find(b => b.innerText.trim() === '详情')
    if (btn) btn.click()
    await new Promise(r => setTimeout(r, 900))
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    return { rows: rows.length, dialog: d ? d.innerText.slice(0, 120).replace(/\n/g, ' | ') : '无' }
  })
  console.log('变更详情:', JSON.stringify(chg))

  // 3) 退租：操作列 & 更多
  await page.evaluate(() => { location.hash = '#/terminations' })
  await sleep(3500)
  console.log('退租操作:', JSON.stringify(await page.evaluate(() => ({
    more: Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('更多')).length,
    enforce: Array.from(document.querySelectorAll('button')).some(b => b.innerText.includes('强制腾退')),
    release: Array.from(document.querySelectorAll('button')).some(b => b.innerText.includes('释放房源'))
  }))))

  // 4) 抄表：按钮与设备带出
  await page.evaluate(() => { location.hash = '#/meter-readings' })
  await sleep(3500)
  console.log('抄表按钮:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).map(b => b.innerText.trim())
      .filter(t => t.includes('录入') || t.includes('批量')))))
  await browser.close()
})()
