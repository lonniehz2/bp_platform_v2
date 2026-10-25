/**
 * 组织五级地址：编辑弹窗回显代码级联 + 社区下拉可手填。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const clickBtn = (page, t) => page.evaluate((text) => {
  const b = Array.from(document.querySelectorAll('button'))
    .filter((x) => (x.innerText || '').trim() === text)
    .find((x) => x.offsetParent !== null)
  if (b) { b.click(); return true }
  return false
}, t)

const lastDialog = (page) => page.evaluate(() => {
  const d = Array.from(document.querySelectorAll('.el-dialog'))
    .filter((x) => x.offsetParent !== null).pop()
  return d ? d.innerText.replace(/\n+/g, ' | ').slice(0, 260) : '无弹窗'
})

const cascaderText = (page) => page.evaluate(() => {
  const d = Array.from(document.querySelectorAll('.el-dialog'))
    .filter((x) => x.offsetParent !== null).pop()
  if (!d) return ''
  const inputs = Array.from(d.querySelectorAll('.el-cascader input'))
  return inputs.map((i) => i.value).filter(Boolean).join(' / ')
})

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 200)))
  page.on('console', (m) => { if (m.type()==='error') console.log('控制台:', m.text().slice(0,200)) })

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

  await page.goto(BASE + '/#/orgs', { waitUntil: 'networkidle2' })
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
  await sleep(2000)

  await page.screenshot({ path: path.join(__dirname, '_shots', 'org-page-state.png') });
  console.log('localStorage:', await page.evaluate(() => JSON.stringify(Object.fromEntries(Object.entries(localStorage).filter(([k]) => k.includes('org') || k.includes('ui'))).slice(0,5))))
  console.log('接口:', await page.evaluate(async () => { const r = await fetch('/api/v1/orgs?pageNum=1&pageSize=5', { headers: { 'X-Tenant-Id': '350600', Authorization: 'Bearer ' + (localStorage.getItem('bp.token') || localStorage.getItem('token') || '') } }); return r.status }))
  console.log('首行:', await page.evaluate(() => {
    const tr = document.querySelector('.el-table__body tr')
    return tr ? tr.innerText.replace(/\n+/g, ' | ').slice(0, 90) : ''
  }))

  console.log('打开编辑:', await clickBtn(page, '编辑'))
  await sleep(1500)
  console.log('弹窗内容:', await lastDialog(page))
  console.log('标准地址回显:', await cascaderText(page))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'org-5level-edit.png') })

  // 社区下拉选项
  const opts = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog'))
      .filter((x) => x.offsetParent !== null).pop()
    if (!d) return []
    const sels = Array.from(d.querySelectorAll('.el-select'))
    const last = sels[sels.length - 1]
    if (!last) return []
    last.querySelector('input')?.click()
    return []
  })
  await sleep(1200)
  const items = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-select-dropdown__item'))
      .map((x) => x.innerText.trim()).slice(0, 8))
  console.log('社区选项:', items.join(' / ') || '（空，可手填）')

  await page.screenshot({ path: path.join(__dirname, '_shots', 'org-5level-community.png') })
  await browser.close()
})()
