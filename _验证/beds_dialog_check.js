/**
 * 床位管理弹窗冒烟：打开房源台账 → 点「床位管理」→ 检查弹窗与表格渲染。
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

  await page.goto(BASE + '/#/houses', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 1800))

  const btn = await page.$('[data-testid="house-beds"]')
  if (!btn) {
    console.log('结论：未找到「床位管理」按钮（异常）')
    await browser.close(); process.exit(1)
  }
  await btn.click()
  await new Promise(r => setTimeout(r, 1200))

  const title = await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-dialog__title'))
      .map(e => e.innerText.trim())
    return t[t.length - 1] || ''
  })
  const hasTreeSelect = await page.evaluate(
    () => !!document.querySelector('.el-dialog .el-select, .el-dialog .el-tree-select'))
  const buttons = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).pop()
    return d ? Array.from(d.querySelectorAll('button')).map(b => b.innerText.trim())
      .filter(Boolean) : []
  })
  await page.screenshot({ path: path.join(shots, 'dorm-beds.png') })

  console.log('弹窗标题:', title)
  console.log('含房间选择:', hasTreeSelect)
  console.log('按钮:', buttons.join(' / '))
  console.log(title.includes('床位') && hasTreeSelect
    ? '结论：床位管理弹窗正常' : '结论：弹窗异常')
  await browser.close()
  process.exit(title.includes('床位') && hasTreeSelect ? 0 : 1)
})()
