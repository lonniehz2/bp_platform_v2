/**
 * 收敛后验证：多页签页面单入口 + 运维台路由仍可直达。
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
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))

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
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2500)

  // 点「系统与数据」→「用户与权限」
  await page.evaluate(() => {
    const g = Array.from(document.querySelectorAll('.rail-item'))
      .find((x) => (x.innerText || '').trim() === '系统与数据')
    if (g) g.click()
  })
  await sleep(900)
  const items = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.panel-menu .el-menu-item'))
      .map((x) => x.innerText.replace(/\s+/g, ' ').trim()))
  console.log('系统与数据菜单(' + items.length + '):', items.join(' / '))

  const clicked = await page.evaluate(() => {
    const it = Array.from(document.querySelectorAll('.panel-menu .el-menu-item'))
      .find((x) => x.innerText.includes('用户与权限'))
    if (!it) return false
    it.click()
    return true
  })
  await sleep(2400)
  const rbac = await page.evaluate(() => ({
    hash: location.hash,
    tabs: Array.from(document.querySelectorAll('.el-tabs__item')).map((x) => x.innerText.trim()).slice(0, 4),
    breadcrumb: document.querySelector('.crumb')?.innerText.replace(/\n+/g, ' / ')
  }))
  console.log('点击用户与权限:', clicked, '→', rbac.hash)
  console.log('页内页签:', rbac.tabs.join(' / '), '| 面包屑:', rbac.breadcrumb)
  await page.screenshot({ path: path.join(__dirname, '_shots', 'menu-collapsed.png') })

  // 运维台直达
  await page.evaluate(() => { location.hash = '#/ops-center' })
  await sleep(2200)
  const ops = await page.evaluate(() => ({
    hash: location.hash,
    tabs: Array.from(document.querySelectorAll('.el-tabs__item')).map((x) => x.innerText.trim())
  }))
  console.log('运维台直达:', ops.hash, '| 页签:', ops.tabs.join(' / '))

  await browser.close()
})()
