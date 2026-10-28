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
  // 在弹窗第一个输入框（HouseSelect）输入房源编号
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    const inp = d && d.querySelector('input')
    if (inp) {
      inp.focus(); inp.value = 'ZZ-H-05771'
      inp.dispatchEvent(new Event('input', { bubbles: true }))
    }
  })
  await sleep(1800)
  const opts = await page.evaluate(() => Array.from(document.querySelectorAll('.el-select-dropdown__item'))
    .map(x => x.innerText.trim()))
  console.log('候选:', JSON.stringify(opts.slice(0, 4)))
  const clicked = await page.evaluate(() => {
    const item = Array.from(document.querySelectorAll('.el-select-dropdown__item'))
      .find(x => x.innerText.includes('ZZ-H-05771'))
    if (item) { item.click(); return true }
    return false
  })
  console.log('选中房源:', clicked)
  await sleep(500)
  console.log('输入值:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    return Array.from(d.querySelectorAll('input')).map(i => i.value)
  })))
  await sleep(900)
  // 打开计量项目下拉（弹窗内第二个 el-select）
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    const sells = d ? Array.from(d.querySelectorAll('.el-select')) : []
    const target = sells[1]
    const w = target && (target.querySelector('.el-select__wrapper') || target)
    if (w) { w.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); w.click() }
  })
  await sleep(900)
  const feeClicked = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.el-select-dropdown__item'))
    const elec = items.find(x => x.innerText.includes('电费')) || items[0]
    if (elec) { elec.click(); return elec.innerText.trim() }
    return null
  })
  console.log('选中项目:', feeClicked)
  await sleep(1600)
  console.log('设备表:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    if (!d) return null
    return { alert: (d.querySelector('.el-alert__title') || {}).innerText,
      heads: Array.from(d.querySelectorAll('th')).map(t => t.innerText.trim()).filter(Boolean),
      rows: Array.from(d.querySelectorAll('.el-table__body tr')).map(tr => tr.innerText.trim()) }
  })))
  await browser.close()
})()
