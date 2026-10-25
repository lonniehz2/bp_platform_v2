/**
 * 角色 / 权限 页签的启用停用按钮验证（直接访问带 tab 的路由）。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const firstRow = (page) => page.evaluate(() => {
  const tr = document.querySelector('.el-table__body tr')
  return tr ? tr.innerText.replace(/\n+/g, ' | ').slice(0, 130) : '无数据'
})

const toggleAndRead = async (page) => {
  const clicked = await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => ['停用', '启用'].includes((x.innerText || '').trim()))
    if (!b) return ''
    const t = (b.innerText || '').trim()
    b.click()
    return t
  })
  await sleep(1600)
  const row = await firstRow(page)
  return { clicked, row }
}

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)

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

  for (const [tab, label] of [['role', '角色'], ['perm', '权限']]) {
    await page.goto(BASE + '/#/rbac/' + tab, { waitUntil: 'networkidle2' })
    await sleep(2600)
    console.log(label + '行:', await firstRow(page))
    const a = await toggleAndRead(page)
    const b = await toggleAndRead(page)
    console.log(label + '切换:', a.clicked, '→ 行:', a.row.slice(0, 60))
    console.log(label + '再切:', b.clicked)
    await page.screenshot({ path: path.join(__dirname, '_shots', 'status-' + tab + '.png') })
  }

  await browser.close()
})()
