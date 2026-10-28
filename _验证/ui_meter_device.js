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
  await page.evaluate(() => { location.hash = '#/meter-readings' })
  await sleep(3500)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('录入读数'))
    if (b) b.click()
  })
  await sleep(900)
  // 房源远程搜索
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    const inp = d && d.querySelector('input')
    if (inp) { inp.focus(); inp.value = 'ZZ-QA-645622'
      inp.dispatchEvent(new Event('input', { bubbles: true })) }
  })
  await sleep(1500)
  const opts = await page.evaluate(() => Array.from(document.querySelectorAll('.el-select-dropdown__item'))
    .map(x => x.innerText.trim()).slice(0, 3))
  console.log('房源候选:', JSON.stringify(opts))
  await page.evaluate(() => {
    const it = document.querySelector('.el-select-dropdown__item')
    if (it) it.click()
  })
  await sleep(800)
  // 选择第一个计量项目
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    const sels = d ? d.querySelectorAll('.el-select') : []
    if (sels.length) {
      const w = sels[0].querySelector('.el-select__wrapper') || sels[0]
      w.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); w.click()
    }
  })
  await sleep(900)
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.el-select-dropdown__item'))
    const water = items.find(x => x.innerText.includes('水费')) || items[0]
    if (water) water.click()
  })
  await sleep(1500)
  console.log('设备表:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    if (!d) return null
    return { rows: d.querySelectorAll('.el-table__body tr').length,
      heads: Array.from(d.querySelectorAll('th')).map(t => t.innerText.trim()).filter(Boolean),
      first: (d.querySelector('.el-table__body tr') || {}).innerText }
  })))
  await browser.close()
})()
