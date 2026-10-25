/**
 * 角色 / 权限 状态切换验证：只读当前激活页签的表格。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const activeRow = (page) => page.evaluate(() => {
  const pane = Array.from(document.querySelectorAll('.el-tab-pane'))
    .find((p) => p.offsetParent !== null)
  if (!pane) return '无激活页签'
  const tr = pane.querySelector('.el-table__body tr')
  return tr ? tr.innerText.replace(/\n+/g, ' | ').slice(0, 130) : '无数据'
})

const toggleActive = (page) => page.evaluate(() => {
  const pane = Array.from(document.querySelectorAll('.el-tab-pane'))
    .find((p) => p.offsetParent !== null)
  if (!pane) return ''
  const b = Array.from(pane.querySelectorAll('button'))
    .find((x) => ['停用', '启用'].includes((x.innerText || '').trim()))
  if (!b) return ''
  const t = (b.innerText || '').trim()
  b.click()
  return t
})

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  page.on('pageerror', (e) => console.log('页面异常:', String(e).slice(0,200)))
  page.on('console', (m) => { if (m.type()==='error') console.log('控制台:', m.text().slice(0,200)) })
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
    await sleep(2800)
    await page.screenshot({ path: path.join(__dirname, '_shots', 'dbg-' + tab + '.png') });
    console.log(label + ' 行:', await activeRow(page), '| 文本:', await page.evaluate(() => document.body.innerText.slice(0,120).replace(/\n+/g,' ')))
    const a = await toggleActive(page); await sleep(1700)
    console.log(label + ' 点击:', a, '→ 行:', await activeRow(page))
    const b = await toggleActive(page); await sleep(1700)
    console.log(label + ' 再点:', b, '→ 行:', await activeRow(page))
    await page.screenshot({ path: path.join(__dirname, '_shots', 'status-' + tab + '.png') })
  }

  await browser.close()
})()
