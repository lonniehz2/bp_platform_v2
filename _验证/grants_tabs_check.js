/**
 * 通行授权页验证：三个页签、授权列表、新建/撤销入口、对账与审计。
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
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 180)))

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
  await page.waitForSelector('.rail', { timeout: 30000 })
  await sleep(2200)

  await page.evaluate(() => { location.hash = '#/grants' })
  await sleep(2800)

  const info = await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('.el-tabs__item')).map((x) => x.innerText.trim())
    const rows = Array.from(document.querySelectorAll('.el-table__body tr')).slice(0, 3)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 90))
    const title = document.querySelector('.page-card h3')?.innerText.trim()
    const buttons = Array.from(document.querySelectorAll('.page-card button'))
      .map((b) => b.innerText.trim()).filter(Boolean).slice(0, 12)
    return { title, tabs, rows, buttons }
  })
  console.log('页面标题:', info.title)
  console.log('页签:', info.tabs.join(' / '))
  console.log('按钮:', info.buttons.join(' | '))
  console.log('首行:', info.rows[0] || '无数据')
  await page.screenshot({ path: path.join(__dirname, '_shots', 'grants-grant-tab.png') })

  // 切到对账差异
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-tabs__item'))
      .find((x) => x.innerText.includes('对账差异'))
    if (t) t.click()
  })
  await sleep(1800)
  const diff = await page.evaluate(() => ({
    rows: document.querySelectorAll('.el-table__body tr').length,
    hasRunBtn: !!Array.from(document.querySelectorAll('button'))
      .find((b) => b.innerText.includes('执行对账'))
  }))
  console.log('对账页签 行数:', diff.rows, ' 执行对账按钮:', diff.hasRunBtn)

  // 切到授权审计
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-tabs__item'))
      .find((x) => x.innerText.includes('授权审计'))
    if (t) t.click()
  })
  await sleep(1600)
  const audit = await page.evaluate(() => document.querySelectorAll('.el-table__body tr').length)
  console.log('审计页签 行数:', audit)
  await page.screenshot({ path: path.join(__dirname, '_shots', 'grants-audit-tab.png') })

  // 入户走访页
  await page.evaluate(() => { location.hash = '#/visits' })
  await sleep(2400)
  const visits = await page.evaluate(() => ({
    title: document.querySelector('.page-card h3')?.innerText.trim(),
    alert: document.querySelector('.el-alert__title')?.innerText.trim().slice(0, 60),
    buttons: Array.from(document.querySelectorAll('.page-card button'))
      .map((b) => b.innerText.trim()).filter(Boolean).slice(0, 8)
  }))
  console.log('走访页 标题:', visits.title, '| 提示:', visits.alert)
  console.log('走访页 按钮:', visits.buttons.join(' / '))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'visits-renamed.png') })

  await browser.close()
})()
