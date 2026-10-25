/**
 * 复现「详情 → 背景变黑」：逐个候选页面点开详情，截图并检测遮罩状态。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')
const fs = require('fs')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
fs.mkdirSync(OUT, { recursive: true })

const PAGES = [
  ['/persons', '人员档案'],
  ['/persons/profile', '保障档案'],
  ['/persons/verify', '实名核验'],
  ['/rbac/users', '用户管理']
]

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)

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

  for (const [url, label] of PAGES) {
    await page.goto(BASE + '/#' + url, { waitUntil: 'networkidle2' })
    await new Promise(r => setTimeout(r, 2400))
    const opened = await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button'))
        .find((x) => x.innerText.trim() === '详情')
      if (b) { b.click(); return true }
      return false
    })
    await new Promise(r => setTimeout(r, 1500))
    const state = await page.evaluate(() => {
      const overlays = Array.from(document.querySelectorAll('.el-overlay'))
        .map((o) => {
          const cs = getComputedStyle(o)
          return {
            display: cs.display, z: cs.zIndex,
            bg: cs.backgroundColor,
            h: o.getBoundingClientRect().height
          }
        })
      return {
        bodyBg: getComputedStyle(document.body).backgroundColor,
        overlays,
        dialogCount: document.querySelectorAll('.el-dialog').length
      }
    })
    const name = url.replace(/[/?]/g, '_')
    await page.screenshot({ path: path.join(OUT, 'dark-' + name + '.png') })
    console.log('%s 有详情按钮=%s 弹窗=%d body背景=%s 遮罩=%s',
      label, opened, state.dialogCount, state.bodyBg, JSON.stringify(state.overlays))
  }

  await browser.close()
})()
