/**
 * 租户账号菜单检查：禁用项、落点页面。
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
    set(0, '350600'); set(1, 'test_tenant'); set(2, 'Test@1234')
  })
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /\u767b\s*\u5f55/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForSelector('.rail, .el-menu', { timeout: 30000 })
  await sleep(3000)

  const landing = await page.evaluate(() => location.hash)
  const info = await page.evaluate(() => {
    const groups = Array.from(document.querySelectorAll('.rail-item span')).map((x) => x.innerText.trim())
    const items = Array.from(document.querySelectorAll('.panel-menu .el-menu-item')).map((x) => ({
      t: x.innerText.replace(/\s+/g, ' ').trim(),
      d: x.classList.contains('is-disabled')
    }))
    return { groups, items: items.length, disabled: items.filter((x) => x.d).length,
      names: items.map((x) => (x.d ? '·' : '✓') + x.t).slice(0, 12) }
  })
  console.log('落点:', landing)
  console.log('分组数:', info.groups.length, '| 当前组菜单:', info.items, '禁用:', info.disabled)
  console.log('明细:', info.names.join(' | '))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'menu-tenant2.png') })
  await browser.close()
})()
