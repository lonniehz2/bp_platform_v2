const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1600, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('PAGEERROR', String(e).slice(0, 120)))
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
  await page.evaluate(() => { location.hash = '#/meter-readings' })
  await sleep(4000)

  // 批量弹窗宽度与列
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('批量录入'))
    if (b) b.click()
  })
  await sleep(1000)
  console.log('批量弹窗:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    if (!d) return null
    return { width: Math.round(d.getBoundingClientRect().width),
      tableWidth: Math.round((d.querySelector('.el-table') || {}).getBoundingClientRect
        ? d.querySelector('.el-table').getBoundingClientRect().width : 0),
      heads: Array.from(d.querySelectorAll('th')).map(t => t.innerText.trim()).filter(Boolean) }
  })))

  // 打开导出
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    const b = d && Array.from(d.querySelectorAll('button')).find(x => x.innerText.includes('导出 CSV'))
    if (b) b.click()
  })
  await sleep(1200)
  console.log('导出弹窗:', JSON.stringify(await page.evaluate(() => {
    const ds = Array.from(document.querySelectorAll('.el-dialog')).filter(x => x.offsetParent)
    const d = ds[ds.length - 1]
    return d ? { text: d.innerText.slice(0, 60).replace(/\n/g, ' | '),
      selects: d.querySelectorAll('.el-select').length,
      orgPlaceholder: !!Array.from(d.querySelectorAll('input')).find(i => i.placeholder === '选择组织') } : null
  })))
  // 组织下拉项
  await page.evaluate(() => {
    const ds = Array.from(document.querySelectorAll('.el-dialog')).filter(x => x.offsetParent)
    const d = ds[ds.length - 1]
    const w = d && d.querySelector('.el-select__wrapper')
    if (w) { w.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); w.click() }
  })
  await sleep(1200)
  console.log('组织选项:', await page.evaluate(() => document.querySelectorAll('.el-select-dropdown__item').length))
  await browser.close()
})()
