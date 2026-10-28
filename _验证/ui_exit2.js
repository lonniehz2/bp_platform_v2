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
  await sleep(2000)
  await page.evaluate(() => { location.hash = '#/persons' })
  await sleep(3000)
  // 切到保障档案
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-tabs__item')).find((x) => x.innerText.includes('保障档案'))
    if (t) t.click()
  })
  await sleep(3000)
  console.log('说明:', await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('.el-alert__title')).map(x=>x.innerText)
    return { count: all.length, hasMine: all.some(t=>t.includes('资格判定：按档案事实')), sample: all.slice(0,3).map(t=>t.slice(0,40)) }
  }))
  const stat = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    const exited = rows.find((tr) => tr.innerText.includes('已退出'))
    let disabled = null
    if (exited) {
      const b = Array.from(exited.querySelectorAll('button')).find((x) => x.innerText.includes('退出保障'))
      disabled = b ? b.disabled : 'no-btn'
    }
    return { rows: rows.length, hasExited: !!exited, exitDisabled: disabled }
  })
  console.log('已退出行/按钮:', JSON.stringify(stat))
  // 点资格判定看确认文案
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '资格判定')
    if (b) b.click()
  })
  await sleep(1000)
  console.log('判定确认:', await page.evaluate(() => {
    const box = document.querySelector('.el-message-box__message')
    return box ? box.innerText.slice(0, 120) : '无'
  }))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-message-box button')).find((x) => x.innerText.includes('取消'))
    if (b) b.click()
  })
  await browser.close()
})()
