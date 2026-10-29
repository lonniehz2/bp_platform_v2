const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1500, height: 950 })
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
  await sleep(300)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('登'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)
  await page.evaluate(() => { location.hash = '#/rbac' })
  await sleep(3000)

  console.log('tabs', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-tabs__item')).map((x) => x.innerText.trim())))

  // click role tab and dump tables
  await page.evaluate(() => {
    const tab = Array.from(document.querySelectorAll('.el-tabs__item')).find((x) => x.innerText.trim() === '角色')
    if (tab) tab.click()
  })
  await sleep(1800)
  console.log('tables', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table')).map((t) => ({
      heads: Array.from(t.querySelectorAll('.el-table__header th')).map((h) => h.innerText.trim()),
      rows: t.querySelectorAll('.el-table__body tr').length
    }))))

  // open role config: find 配置 in visible buttons
  console.log('config btns', await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).filter((b) => b.offsetParent && b.innerText.trim() === '配置').length))
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).filter((b) => b.offsetParent)
      .find((x) => x.innerText.trim() === '配置')
    if (btn) btn.click()
  })
  await sleep(1500)
  console.log('dialogs', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-dialog')).filter((d) => d.offsetParent).map((d) => ({
      title: d.querySelector('.el-dialog__title')?.innerText,
      tabs: Array.from(d.querySelectorAll('.el-tabs__item')).map((x) => x.innerText.trim()),
      labels: Array.from(d.querySelectorAll('.perm-actions .el-checkbox__label')).map((x) => x.innerText.trim()).slice(0, 5)
    }))))
  await b.close()
})()
