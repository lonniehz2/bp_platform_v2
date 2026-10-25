/**
 * 用户管理：详情 / 编辑 打开后与关闭后的遮罩状态检查。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const overlayState = (page) => page.evaluate(() => {
  const list = Array.from(document.querySelectorAll('.el-overlay'))
  const visible = list.filter((o) => getComputedStyle(o).display !== 'none')
  return {
    total: list.length,
    visible: visible.length,
    zs: visible.map((o) => getComputedStyle(o).zIndex),
    dialogs: document.querySelectorAll('.el-dialog').length,
    visibleDialogs: Array.from(document.querySelectorAll('.el-dialog'))
      .filter((d) => d.offsetParent !== null).length
  }
})

const clickBtn = (page, text) => page.evaluate((t) => {
  const b = Array.from(document.querySelectorAll('button'))
    .filter((x) => (x.innerText || '').trim() === t)
    .find((x) => x.offsetParent !== null)
  if (b) { b.click(); return true }
  return false
}, text)

const closeTopDialog = (page) => page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll('.el-dialog__headerbtn'))
    .filter((b) => b.offsetParent !== null)
  if (!btns.length) return false
  btns[btns.length - 1].click()
  return true
})

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))

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

  await page.goto(BASE + '/#/rbac/users', { waitUntil: 'networkidle2' })
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
  await sleep(1800)

  console.log('打开前:', JSON.stringify(await overlayState(page)))

  console.log('点详情:', await clickBtn(page, '详情'))
  await sleep(1200)
  console.log('详情打开:', JSON.stringify(await overlayState(page)))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'user-detail-open.png') })

  console.log('关闭:', await closeTopDialog(page))
  await sleep(1200)
  console.log('详情关闭后:', JSON.stringify(await overlayState(page)))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'user-detail-closed.png') })

  console.log('点编辑:', await clickBtn(page, '编辑'))
  await sleep(1200)
  console.log('编辑打开:', JSON.stringify(await overlayState(page)))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'user-edit-open.png') })
  console.log('关闭:', await closeTopDialog(page))
  await sleep(1200)
  console.log('编辑关闭后:', JSON.stringify(await overlayState(page)))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'user-edit-closed.png') })

  await browser.close()
})()
