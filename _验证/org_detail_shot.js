/**
 * 单页：组织详情截图（含标准地址）。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('页面错误:', String(e).slice(0, 120)))

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
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
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
  await page.goto(BASE + '/#/orgs', { waitUntil: 'networkidle2' })
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
  await sleep(1500)

  const ok = await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.trim() === '详情')
    if (b) { b.click(); return true }
    return false
  })
  await sleep(1200)
  const text = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).pop()
    return d ? d.innerText.replace(/\n+/g, ' | ') : '无弹窗'
  })
  await page.screenshot({ path: path.join(__dirname, '_shots', 'fix-org-detail.png') })
  console.log('详情点击:', ok)
  console.log(text.slice(0, 220))
  await browser.close()
})()
