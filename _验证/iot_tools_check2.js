// IoT 联调工具页验证
const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1150 })
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

  await page.evaluate(() => { location.hash = '#/iot-tools' })
  await sleep(3200)
  const info = await page.evaluate(() => ({
    title: document.querySelector('h3')?.innerText,
    tabs: Array.from(document.querySelectorAll('.el-tabs__item')).map((x) => x.innerText.trim()),
    labels: Array.from(document.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim())
  }))
  console.log('页面:', info.title, '| 页签:', info.tabs.join(' / '))
  console.log('表单:', info.labels.join(' | '))

  // 计算签名
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('计算签名'))
    if (b) b.click()
  })
  await sleep(1500)
  const signed = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-descriptions__label, .el-descriptions__content'))
      .map((x) => x.innerText.trim())
    return rows.slice(0, 6)
  })
  console.log('签名结果:', JSON.stringify(signed).slice(0, 220))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'iot-tools-sign.png') })

  // 切到凭据同步
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-tabs__item')).find((x) => x.innerText.includes('凭据同步'))
    if (t) t.click()
  })
  await sleep(2000)
  const cred = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr')).slice(0, 3)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 100))
    return { count: document.querySelectorAll('.el-table__body tr').length, rows }
  })
  console.log('凭据同步页签:', cred.count, '行')
  cred.rows.forEach((r) => console.log('  ', r))

  // 切到回调日志
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-tabs__item')).find((x) => x.innerText.includes('回调日志'))
    if (t) t.click()
  })
  await sleep(2200)
  const logs = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr')).slice(0, 2)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 120))
    return { count: document.querySelectorAll('.el-table__body tr').length, rows }
  })
  console.log('回调日志行数:', logs.count)
  logs.rows.forEach((r) => console.log('  ', r))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'iot-tools-logs.png') })

  await browser.close()
})()
