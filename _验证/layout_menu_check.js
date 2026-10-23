/**
 * 对比两种布局的菜单渲染：风格1（classic）与风格2（rail）。
 * 输出：分组数、面板菜单数、控制台错误。
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const shots = path.join(__dirname, '_shots')
fs.mkdirSync(shots, { recursive: true })

async function run(style) {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new', args: ['--no-sandbox']
  })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  const errors = []
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text().slice(0, 160)) })
  page.on('pageerror', (e) => errors.push('PAGEERROR ' + String(e).slice(0, 160)))

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
  await page.waitForFunction(
    () => !!document.querySelector('.rail, .el-menu, .aside'), { timeout: 20000 })
  await page.evaluate((s) => localStorage.setItem('bp.ui.style', s), style)
  await page.reload({ waitUntil: 'networkidle2' })
  await page.goto(BASE + '/#/dashboard', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 1800))

  const out = {
    style,
    rail: await page.$('.rail').then(Boolean),
    railItems: await page.$$eval('.rail-item', els => els.length).catch(() => 0),
    groups: await page.$$eval('.rail-item span', els => els.map(e => e.innerText.trim())).catch(() => []),
    menuItems: await page.$$eval('.el-menu-item', els => els.map(e => e.innerText.trim())).catch(() => []),
    asideItems: await page.$$eval('.aside .el-menu-item, .aside-menu .el-menu-item, .menu .el-menu-item',
      els => els.map(e => e.innerText.trim())).catch(() => []),
    errors
  }
  await page.screenshot({ path: path.join(shots, 'layout-' + style + '.png') })
  await browser.close()
  return out
}

;(async () => {
  for (const s of ['classic', 'rail']) {
    const r = await run(s)
    console.log('=== ' + s + ' ===')
    console.log('  rail 外壳 :', r.rail, ' 左侧图标数:', r.railItems)
    console.log('  分组名   :', r.groups.slice(0, 6).join(' / ') || '(空)')
    console.log('  菜单项   :', r.menuItems.length, r.menuItems.slice(0, 5).join(' / '))
    console.log('  侧栏菜单 :', r.asideItems.length, r.asideItems.slice(0, 5).join(' / '))
    if (r.errors.length) console.log('  控制台错误:', r.errors.slice(0, 3).join(' | '))
  }
})()
