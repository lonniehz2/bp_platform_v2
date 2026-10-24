/**
 * 菜单展开状态检查：不同角色登录后，默认展开的分组应当不同，且能记忆手动选择。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')
const fs = require('fs')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const shots = path.join(__dirname, '_shots')
fs.mkdirSync(shots, { recursive: true })

const ACCOUNTS = [
  ['admin', 'admin123', '系统管理员'],
  ['test_finance', 'Test@1234', '财务岗'],
  ['test_tenant', 'Test@1234', '租户']
]

async function openGroupsOf(page) {
  return page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-sub-menu.is-opened'))
      .map(e => e.querySelector('.el-sub-menu__title')?.innerText.trim())
      .filter(Boolean))
}

async function run(user, pwd, label) {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('console', (m) => {
    const t = m.text()
    if (t.indexOf('MENUDBG') >= 0 || m.type() === 'error') console.log('   [console] ' + t.slice(0,200))
  })

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await page.evaluate(() => localStorage.clear())
  await page.reload({ waitUntil: 'networkidle2' })
  await page.evaluate((u, p) => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600'); set(1, u); set(2, p)
  }, user, pwd)
  await new Promise(r => setTimeout(r, 300))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail, .el-menu, .aside'), { timeout: 20000 })
  await page.goto(BASE + '/#/dashboard', { waitUntil: 'networkidle2' })
  await page.evaluate(() => localStorage.setItem('bp.ui.style', 'classic'))
  await page.reload({ waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 4500))

  const opened = await openGroupsOf(page)
  if (process.env.DUMP === '1') {
    const dump = await page.evaluate(() => Array.from(document.querySelectorAll('.el-sub-menu'))
      .slice(0,4).map(e => e.className))
    console.log('   [class] ' + JSON.stringify(dump))
  }
  await page.screenshot({ path: path.join(shots, 'menu-pref-' + user + '.png') })

  // 手动收起第一个展开的分组，刷新后应记住
  const before = opened.length
  if (before > 0) {
    const titles = await page.$$('.el-sub-menu__title')
    for (const t of titles) {
      const txt = await page.evaluate(e => e.innerText.trim(), t)
      if (txt === opened[0]) { await t.click(); break }
    }
    await new Promise(r => setTimeout(r, 800))
    await page.reload({ waitUntil: 'networkidle2' })
    await new Promise(r => setTimeout(r, 2000))
  }
  const afterReload = await openGroupsOf(page)

  await browser.close()
  return { label, opened, afterReload }
}

;(async () => {
  for (const [u, p, label] of ACCOUNTS) {
    const r = await run(u, p, label)
    console.log('%s(%s) 默认展开 %d 组: %s', label, u, r.opened.length, r.opened.join(' / '))
    console.log('   刷新后: %d 组: %s', r.afterReload.length, r.afterReload.join(' / '))
  }
})()
