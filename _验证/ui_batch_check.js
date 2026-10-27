// 本轮修复的界面验证
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

  // 人员：建档弹窗
  await page.evaluate(() => { location.hash = '#/persons' })
  await sleep(3200)
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('.el-tabs__item'))
    const t = tabs.find((x) => x.innerText.includes('保障档案') || x.innerText.includes('保障建档'))
    if (t) t.click()
  })
  await sleep(1500)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '建档')
    if (b) b.click()
  })
  await sleep(1200)
  const profile = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return {
      labels: Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim()).slice(0, 6),
      hasSelect: d.querySelectorAll('.el-select').length
    }
  })
  console.log('建档弹窗:', JSON.stringify(profile))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'profile-person-picker.png') })
  await page.keyboard.press('Escape'); await sleep(600)

  // 轮候入队
  await page.evaluate(() => { location.hash = '#/waitlist' })
  await sleep(3000)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('入队登记'))
    if (b) b.click()
  })
  await sleep(1200)
  const enq = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim())
  })
  console.log('入队弹窗:', JSON.stringify(enq))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'waitlist-enqueue.png') })
  await page.keyboard.press('Escape'); await sleep(500)

  // 新增房源
  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(3200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新增房源'))
    if (b) b.click()
  })
  await sleep(1800)
  const house = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return {
      labels: Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim()).slice(0, 5),
      treeItems: d.querySelectorAll('.el-tree-node').length,
      selectValues: Array.from(d.querySelectorAll('input')).map((x) => x.value).filter(Boolean).slice(0, 4)
    }
  })
  console.log('新增房源:', JSON.stringify(house))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'house-create-org.png') })

  await browser.close()
})()
