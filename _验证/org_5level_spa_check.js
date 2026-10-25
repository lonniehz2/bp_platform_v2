/**
 * 组织五级地址验证（SPA 内跳转，避免整页刷新丢失登录态）。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const gotoHash = async (page, hash) => {
  await page.evaluate((h) => { location.hash = h }, hash)
  await sleep(2500)
}

const lastDialogText = (page) => page.evaluate(() => {
  const d = Array.from(document.querySelectorAll('.el-dialog'))
    .filter((x) => x.offsetParent !== null).pop()
  return d ? d.innerText.replace(/\n+/g, ' | ').slice(0, 320) : '无弹窗'
})

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
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })

  await gotoHash(page, '#/orgs')
  await sleep(2500)
  const rows = await page.evaluate(() => document.querySelectorAll('.el-table__body tr').length)
  console.log('组织行数:', rows)

  const opened = await page.evaluate(() => {
    const trs = Array.from(document.querySelectorAll('.el-table__body tr'))
    const tr = trs.find((t) => t.innerText.includes('演示小区')) || trs[0]
    if (!tr) return false
    const b = Array.from(tr.querySelectorAll('button'))
      .find((x) => (x.innerText || '').trim() === '编辑')
    if (!b) return false
    b.click()
    return true
  })
  await sleep(1500)
  console.log('打开编辑:', opened)
  console.log('弹窗:', await lastDialogText(page))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'org-5level-edit.png') })

  // 社区下拉选项
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog'))
      .filter((x) => x.offsetParent !== null).pop()
    if (!d) return
    const sels = Array.from(d.querySelectorAll('.el-select'))
    const last = sels[sels.length - 1]
    if (last) { const inp = last.querySelector('input'); if (inp) inp.click() }
  })
  await sleep(1200)
  const items = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-select-dropdown__item'))
      .map((x) => x.innerText.trim()).slice(0, 10))
  console.log('社区选项:', items.join(' / ') || '（空，可手填）')
  await page.screenshot({ path: path.join(__dirname, '_shots', 'org-5level-community.png') })

  await browser.close()
})()
