/**
 * 组织新增弹窗：地址级联是否加载 + 审计日志枚举是否中文。
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
  const logs = []
  page.on('console', (m) => logs.push(m.text().slice(0, 140)))
  page.on('response', async (r) => {
    if (r.url().includes('/sys/regions/children')) {
      logs.push('REGION ' + r.status() + ' ' + r.url().slice(-60))
    }
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

  await page.goto(BASE + '/#/orgs', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))

  // 打开新增组织
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('新增组织'))
    b && b.click()
  })
  await new Promise(r => setTimeout(r, 1200))

  // 点击地址级联
  const clicked = await page.evaluate(() => {
    const inputs = Array.from(document.querySelectorAll('.el-dialog input'))
    const t = inputs.find((i) => (i.placeholder || '').includes('省'))
    if (!t) return false
    t.click()
    return true
  })
  await new Promise(r => setTimeout(r, 1800))

  const items = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-cascader-node__label'))
      .map((x) => x.innerText.trim()).slice(0, 8))
  await page.screenshot({ path: path.join(shots, 'org-region.png') })
  console.log('点击级联:', clicked, ' 选项数:', items.length)
  console.log('前几项:', items.join(' / '))
  console.log('相关日志:', logs.filter((l) => l.includes('REGION')).slice(0, 3).join(' | ') || '无')

  // 审计日志枚举
  await page.goto(BASE + '/#/sys/audit', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2200))
  const audit = await page.evaluate(() => {
    const t = document.querySelector('.el-table__body tr')
    return t ? t.innerText.replace(/\n+/g, ' | ').slice(0, 160) : '无数据'
  })
  console.log('审计首行:', audit)
  await browser.close()
})()
