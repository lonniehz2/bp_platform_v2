/**
 * 组织/用户 操作按钮端到端验证：
 *  - 组织：详情弹窗、编辑保存、停用→启用
 *  - 用户：详情弹窗、停用→启用
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'

const clickByText = async (page, text) => page.evaluate((t) => {
  const b = Array.from(document.querySelectorAll('button'))
    .find((x) => x.innerText.trim() === t)
  if (b) { b.click(); return true }
  return false
}, text)

const dialogText = async (page) => page.evaluate(() => {
  const d = Array.from(document.querySelectorAll('.el-dialog')).pop()
  return d ? d.innerText.replace(/\n+/g, ' | ').slice(0, 120) : '无弹窗'
})

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

  // ---- 组织 ----
  await page.goto(BASE + '/#/orgs', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))
  console.log('组织-详情:', await clickByText(page, '详情'), (await new Promise(r => setTimeout(r, 900)), await dialogText(page)))
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog__headerbtn')).pop()
    d && d.click()
  })
  await new Promise(r => setTimeout(r, 500))

  console.log('组织-编辑:', await clickByText(page, '编辑'),
    (await new Promise(r => setTimeout(r, 900)), await dialogText(page)))
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog__headerbtn')).pop()
    d && d.click()
  })
  await new Promise(r => setTimeout(r, 500))

  // 停用 → 启用
  const t1 = await clickByText(page, '停用')
  await new Promise(r => setTimeout(r, 1400))
  const statusAfterOff = await page.evaluate(() => {
    const tr = document.querySelector('.el-table__body tr')
    return tr ? tr.innerText.replace(/\n+/g, ' | ').slice(0, 90) : ''
  })
  const t2 = await clickByText(page, '启用')
  await new Promise(r => setTimeout(r, 1400))
  console.log('组织-停用:', t1, '后状态行:', statusAfterOff)
  console.log('组织-启用:', t2)

  // ---- 用户 ----
  await page.goto(BASE + '/#/rbac/users', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))
  console.log('用户-详情:', await clickByText(page, '详情'),
    (await new Promise(r => setTimeout(r, 900)), await dialogText(page)))
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog__headerbtn')).pop()
    d && d.click()
  })
  await new Promise(r => setTimeout(r, 500))
  const ut1 = await clickByText(page, '停用')
  await new Promise(r => setTimeout(r, 1400))
  const ut2 = await clickByText(page, '启用')
  await new Promise(r => setTimeout(r, 1200))
  console.log('用户-停用/启用:', ut1, ut2)

  await browser.close()
})()
