/**
 * 抄表管理页检查：打开页面，输出控制台错误与表格行数。
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
  const errors = []
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text().slice(0, 160)) })
  page.on('response', (r) => {
    if (r.status() >= 400) errors.push(r.status() + ' ' + r.url().slice(-70))
  })

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
  await page.goto(BASE + '/#/energy', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 6000))

  const info = await page.evaluate(() => {
    const svgs = Array.from(document.querySelectorAll('svg'))
    return {
      svgCount: svgs.length,
      boxes: svgs.map((s) => { const r = s.getBoundingClientRect(); return Math.round(r.width) + 'x' + Math.round(r.height) }),
      html: (document.querySelector('.trend') || {}).outerHTML?.slice(0, 200) || 'no .trend'
    }
  })
  console.log('SVG:', info.svgCount, info.boxes, info.html)
  const info2 = await page.evaluate(() => ({
    rows: document.querySelectorAll('.el-table__body tr').length,
    empty: (document.querySelector('.el-table__empty-text') || {}).innerText || '',
    text: document.body.innerText.replace(/\n+/g, ' | ').slice(0, 200)
  }))
  await page.screenshot({ path: path.join(shots, 'energy.png') })
  console.log('行数:', info.rows, ' 空提示:', info.empty)
  console.log('文本:', info.text)
  console.log('错误:', errors.slice(0, 4).join(' || ') || '无')
  await browser.close()
})()
