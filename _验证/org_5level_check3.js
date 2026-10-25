/**
 * 通过 API 登录并直接写入 localStorage（避开登录表单索引问题），
 * 再验证组织页列表与编辑弹窗（五级地址）。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const lastDialog = (page) => page.evaluate(() => {
  const d = Array.from(document.querySelectorAll('.el-dialog'))
    .filter((x) => x.offsetParent !== null).pop()
  return d ? d.innerText.replace(/\n+/g, ' | ').slice(0, 300) : '无弹窗'
})

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 200)))

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })

  const token = await page.evaluate(async () => {
    const r = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Tenant-Id': '350600' },
      body: JSON.stringify({ tenantCode: '350600', username: 'admin', password: 'admin123' })
    })
    const d = await r.json()
    const t = d?.data?.token || ''
    if (t) {
      localStorage.setItem('bp_token', t)
      localStorage.setItem('bp_tenant', '350600')
    }
    return t ? 'ok' : JSON.stringify(d).slice(0, 120)
  })
  console.log('登录:', token)

  await page.goto(BASE + '/#/orgs', { waitUntil: 'networkidle2' })
  await sleep(3000)
  const rows = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table__body tr')).length)
  console.log('表格行数:', rows)

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
  console.log('弹窗:', await lastDialog(page))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'org-5level-edit.png') })

  // 社区下拉
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog'))
      .filter((x) => x.offsetParent !== null).pop()
    const sels = Array.from(d.querySelectorAll('.el-select'))
    sels[sels.length - 1]?.querySelector('input')?.click()
  })
  await sleep(1200)
  const items = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-select-dropdown__item'))
      .map((x) => x.innerText.trim()).slice(0, 8))
  console.log('社区选项:', items.join(' / ') || '（空，可手填）')
  await page.screenshot({ path: path.join(__dirname, '_shots', 'org-5level-community.png') })

  await browser.close()
})()
