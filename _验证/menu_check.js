/**
 * 菜单结构冒烟：展开全部分组，输出「分组 → 菜单项」结构。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')
const fs = require('fs')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const shots = path.join(__dirname, '_shots')
fs.mkdirSync(shots, { recursive: true })

async function run(style) {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1100 })

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
  await page.evaluate((s) => localStorage.setItem('bp.ui.style', s), style)
  await page.reload({ waitUntil: 'networkidle2' })
  await page.goto(BASE + '/#/dashboard', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2000))

  const titles = await page.$$('.el-sub-menu__title')
  for (const t of titles) {
    try { await t.click() } catch (e) { /* 忽略 */ }
    await new Promise(r => setTimeout(r, 150))
  }
  await new Promise(r => setTimeout(r, 800))

  const data = await page.evaluate(() => {
    const groups = {}
    for (const sub of Array.from(document.querySelectorAll('.el-sub-menu'))) {
      const name = sub.querySelector('.el-sub-menu__title')?.innerText.trim()
      if (!name) continue
      groups[name] = Array.from(sub.querySelectorAll('.el-menu-item'))
        .map(e => e.innerText.trim().split('\n')[0])
    }
    const railGroups = Array.from(document.querySelectorAll('.rail-item span'))
      .map(e => e.innerText.trim()).filter(Boolean)
    return { groups, railGroups }
  })

  await page.screenshot({ path: path.join(shots, 'menu-' + style + '.png') })
  await browser.close()
  return data
}

;(async () => {
  for (const style of ['classic', 'rail']) {
    const r = await run(style)
    const names = Object.keys(r.groups)
    console.log('=== ' + style + ' ===')
    console.log('  分组数: ' + (style === 'rail' ? r.railGroups.length : names.length))
    if (style === 'rail') console.log('  分组: ' + r.railGroups.join(' / '))
    let total = 0
    for (const g of names) {
      const items = r.groups[g]
      total += items.length
      console.log('  [' + g + '] ' + items.join(' / '))
    }
    console.log('  菜单项合计: ' + total)
  }
})()
