/**
 * 角标与规则明细中文展示检查。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1400 })
  await page.setCacheEnabled(false)

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
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
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(3000)

  // 进入设备与通行分组，读角标
  await page.evaluate(() => {
    const groups = Array.from(document.querySelectorAll('.rail button, .rail .group, .rail div'))
      .find((x) => (x.innerText || '').trim() === '设备与通行')
    if (groups) groups.click()
  })
  await sleep(1500)
  const badges = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-badge__content, .menu-badge, .badge'))
      .map((x) => x.innerText.trim()).filter(Boolean))
  console.log('角标数字:', badges.join(','))
  await page.screenshot({ path: path.join(OUT, 'fb-badge.png') })

  // 规则明细中文
  await page.evaluate(() => { location.hash = '#/alerts' })
  await sleep(4000)
  await page.evaluate(() => {
    const c = Array.from(document.querySelectorAll('.page-card'))
      .find((x) => (x.querySelector('h4')?.innerText || '').includes('规则引擎'))
    if (c) c.scrollIntoView()
  })
  await sleep(800)
  const ruleRows = await page.evaluate(() => {
    const c = Array.from(document.querySelectorAll('.page-card'))
      .find((x) => (x.querySelector('h4')?.innerText || '').includes('规则引擎'))
    if (!c) return []
    const tables = c.querySelectorAll('.el-table')
    const t = tables[1]
    if (!t) return []
    return Array.from(t.querySelectorAll('.el-table__body tr')).slice(0, 4)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 120))
  })
  console.log('规则明细:', JSON.stringify(ruleRows))
  await page.screenshot({ path: path.join(OUT, 'fb-rules-table.png') })

  await browser.close()
})()
