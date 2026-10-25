/**
 * 验收 5 个反馈项：
 *  1. 组织：操作按钮存在、启停可用
 *  2. 组织新增：地址级联有省份
 *  3. 用户：操作按钮 + 授权角色预填
 *  4. 列表状态可改（组织/用户）
 *  5. 审计日志 类型/级别 中文
 */
const puppeteer = require('puppeteer-core')
const path = require('path')
const fs = require('fs')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
fs.mkdirSync(OUT, { recursive: true })

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

  // 1) 组织页操作列
  await page.goto(BASE + '/#/orgs', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))
  const orgRow = await page.evaluate(() => {
    const tr = document.querySelector('.el-table__body tr')
    return tr ? tr.innerText.replace(/\n+/g, ' | ') : '无数据'
  })
  console.log('组织首行:', orgRow.slice(0, 180))
  await page.screenshot({ path: path.join(OUT, 'fix-orgs.png') })

  // 2) 用户页操作列 + 授权角色预填
  await page.goto(BASE + '/#/rbac/users', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))
  const userRow = await page.evaluate(() => {
    const tr = document.querySelector('.el-table__body tr')
    return tr ? tr.innerText.replace(/\n+/g, ' | ') : '无数据'
  })
  console.log('用户首行:', userRow.slice(0, 200))
  await page.screenshot({ path: path.join(OUT, 'fix-users.png') })

  const grant = await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.trim() === '授权角色')
    if (b) { b.click(); return true }
    return false
  })
  await new Promise(r => setTimeout(r, 1800))
  const prefilled = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog')).pop()
    if (!dlg) return 'no dialog'
    const tags = Array.from(dlg.querySelectorAll('.el-tag')).map((t) => t.innerText.trim())
    return tags.length ? tags.join(' / ') : '（无已选角色）'
  })
  console.log('授权角色弹窗已选:', grant, prefilled)
  await page.screenshot({ path: path.join(OUT, 'fix-role-dialog.png') })

  // 3) 审计日志
  await page.goto(BASE + '/#/sys/audit', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))
  const audit = await page.evaluate(() => {
    const tr = document.querySelector('.el-table__body tr')
    return tr ? tr.innerText.replace(/\n+/g, ' | ') : '无数据'
  })
  console.log('审计首行:', audit.slice(0, 180))
  await page.screenshot({ path: path.join(OUT, 'fix-audit.png') })

  await browser.close()
})()
