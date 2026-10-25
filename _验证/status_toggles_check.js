/**
 * 四个页面「启用/停用」按钮端到端验证（通过点击页签切换）。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const rowText = (page) => page.evaluate(() => {
  const tr = document.querySelector('.el-table__body tr')
  return tr ? tr.innerText.replace(/\n+/g, ' | ').slice(0, 140) : '无数据'
})

const clickToggle = (page) => page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll('button'))
    .filter((b) => ['停用', '启用'].includes((b.innerText || '').trim()))
  if (!btns.length) return ''
  const t = (btns[0].innerText || '').trim()
  btns[0].click()
  return t
})

const clickTab = (page, label) => page.evaluate((l) => {
  const tab = Array.from(document.querySelectorAll('.el-tabs__item'))
    .find((x) => (x.innerText || '').trim() === l)
  if (tab) { tab.click(); return true }
  return false
}, label)

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(700)
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

  // ---- 角色 ----
  await page.goto(BASE + '/#/rbac', { waitUntil: 'networkidle2' })
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
  await sleep(1200)
  console.log('角色页签:', await clickTab(page, '角色'))
  await sleep(1500)
  console.log('角色行:', await rowText(page))
  const r1 = await clickToggle(page); await sleep(1600)
  const r2 = await clickToggle(page); await sleep(1400)
  console.log('角色切换:', r1, '->', r2)

  // ---- 权限 ----
  console.log('权限页签:', await clickTab(page, '权限'))
  await sleep(1800)
  const p1 = await clickToggle(page); await sleep(1600)
  const p2 = await clickToggle(page); await sleep(1400)
  console.log('权限切换:', p1, '->', p2)

  // ---- 数据字典 ----
  await page.goto(BASE + '/#/sys/dict', { waitUntil: 'networkidle2' })
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
  await sleep(1500)
  const d1 = await clickToggle(page); await sleep(1600)
  const d2 = await clickToggle(page); await sleep(1400)
  console.log('字典切换:', d1, '->', d2)

  // ---- 开放平台 ----
  await page.goto(BASE + '/#/open', { waitUntil: 'networkidle2' })
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
  await sleep(1500)
  const a1 = await clickToggle(page); await sleep(1600)
  const a2 = await clickToggle(page); await sleep(1400)
  console.log('应用切换:', a1, '->', a2)
  await page.screenshot({ path: path.join(__dirname, '_shots', 'status-open.png') })

  await browser.close()
})()
