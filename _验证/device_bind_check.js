/**
 * 设备类型筛选与绑定页验证（多类型数据）。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')
const fs = require('fs')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const shots = path.join(__dirname, '_shots')
fs.mkdirSync(shots, { recursive: true })

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await new Promise(r => setTimeout(r, 300))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail, .el-menu, .aside'),
    { timeout: 20000 })
  await page.goto(BASE + '/#/devices', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))

  const total0 = await page.evaluate(() =>
    (document.querySelector('.el-pagination__total')?.innerText || '')
      .replace(/[^0-9]/g, ''))

  // 选择「水表」
  const picked = await page.evaluate(() => {
    const sels = Array.from(document.querySelectorAll('.el-select'))
    const t = sels.find((x) => (x.querySelector('input')?.placeholder || '').includes('设备类型'))
    if (!t) return '未找到类型下拉'
    t.click()
    return 'ok'
  })
  await new Promise(r => setTimeout(r, 700))
  const opt = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.el-select-dropdown__item'))
    const o = items.find((x) => (x.innerText || '').includes('水表'))
    if (!o) return '未找到水表选项'
    o.click()
    return 'ok'
  })
  await new Promise(r => setTimeout(r, 2200))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '查询')
    b && b.click()
  })
  await new Promise(r => setTimeout(r, 2200))

  const info = await page.evaluate(() => ({
    total: (document.querySelector('.el-pagination__total')?.innerText || '')
      .replace(/[^0-9]/g, ''),
    rows: Array.from(document.querySelectorAll('.el-table__body tr')).slice(0, 3)
      .map((tr) => tr.innerText.replace(/\n+/g, ' | ')),
    types: Array.from(document.querySelectorAll('.el-table__body tr'))
      .slice(0, 5).map((tr) => tr.querySelectorAll('td')[2]?.innerText.trim())
  }))
  await page.screenshot({ path: path.join(shots, 'devices-water.png') })

  console.log('初始总数:', total0, ' 下拉:', picked, ' 选项:', opt)
  console.log('筛选后总数:', info.total, ' 类型列:', info.types.join(' / '))
  info.rows.forEach((r) => console.log('   ' + r))
  const ok = info.total && info.total !== total0 && info.types.every((t) => t === '水表')
  console.log(ok ? '结论：类型筛选生效' : '结论：类型筛选未生效')
  await browser.close()
  process.exit(ok ? 0 : 1)
})()
