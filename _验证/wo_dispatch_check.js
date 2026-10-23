/**
 * 工单自动派单冒烟：打开工单页 → 检查「批量派单」按钮 → 点第一条待派单的「自动派单」。
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
  await page.setViewport({ width: 1440, height: 900 })

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
  await page.goto(BASE + '/#/workorders', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2000))

  const hasBatch = await page.$('[data-testid="wo-autoassign-all"]').then(Boolean)
  const rowBtns = await page.$$('[data-testid="wo-autoassign"]')
  console.log('批量派单按钮:', hasBatch, ' 行内派单按钮:', rowBtns.length)

  let msg = ''
  if (rowBtns.length) {
    await rowBtns[0].click()
    await new Promise(r => setTimeout(r, 1500))
    msg = await page.evaluate(() => {
      const m = document.querySelector('.el-message--success, .el-message--error')
      return m ? m.innerText.trim() : ''
    })
  }
  await page.screenshot({ path: path.join(shots, 'wo-autoassign.png') })
  console.log('派单提示:', msg || '(无)')
  console.log(hasBatch && (rowBtns.length > 0)
    ? '结论：自动派单入口就绪' : '结论：入口缺失或无可派单工单')
  await browser.close()
  process.exit(hasBatch ? 0 : 1)
})()
