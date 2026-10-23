/**
 * 风格2（rail）左侧菜单冒烟：切到 rail 后检查左侧图标栏与二级面板是否有菜单项。
 * 用法：node rail_menu_check.js
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const shots = path.join(__dirname, '_shots')
fs.mkdirSync(shots, { recursive: true })

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage']
  })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.evaluateOnNewDocument(() => {
    localStorage.setItem('bp.ui.style', 'rail')
  })

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  const n = await page.evaluate(() => document.querySelectorAll('input').length)
  if (n < 3) throw new Error('登录表单结构不符，输入框数=' + n)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus()
      el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600')
    set(1, 'admin')
    set(2, 'admin123')
  })
  await new Promise(r => setTimeout(r, 300))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(
    () => !!document.querySelector('.rail, .el-menu, .aside'), { timeout: 20000 })
  await page.evaluate(() => localStorage.setItem('bp.ui.style', 'rail'))
  await page.goto(BASE + '/#/dashboard', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 1500))

  const style = await page.evaluate(() => localStorage.getItem('bp.ui.style'))
  const railItems = await page.$$eval('.rail-item', els => els.map(e => e.innerText.trim()).filter(Boolean))
  const panelItems = await page.$$eval('.panel-menu .el-menu-item', els => els.map(e => e.innerText.trim()))
  const panelTitle = await page.$eval('.panel-title', e => e.innerText.trim()).catch(() => '')
  const hasRail = await page.$('.rail').then(Boolean)
  const url = page.url()
  const bodyText = (await page.evaluate(() => document.body.innerText || '')).slice(0, 120)
  const menuCount = await page.$$eval('.el-menu-item', els => els.length).catch(() => 0)

  await page.screenshot({ path: path.join(shots, 'rail-menu.png') })

  console.log('当前 URL :', url)
  console.log('风格设置 :', style)
  console.log('页面文本 :', bodyText.replace(/\n/g, ' | '))
  console.log('el-menu 项:', menuCount)
  console.log('rail 外壳:', hasRail)
  console.log('左侧分组 :', railItems.length, railItems.slice(0, 6).join(' / '))
  console.log('面板标题 :', panelTitle)
  console.log('面板菜单 :', panelItems.length, panelItems.slice(0, 6).join(' / '))
  console.log(panelItems.length > 0 ? '结论：风格2 菜单正常' : '结论：风格2 菜单为空（异常）')

  await browser.close()
  process.exit(panelItems.length > 0 ? 0 : 1)
})()
