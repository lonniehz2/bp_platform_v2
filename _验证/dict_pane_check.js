/**
 * 数据字典页：只在激活页签内点击启停，并读取该行状态变化。
 */
const puppeteer = require('puppeteer-core')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const paneInfo = (page) => page.evaluate(() => {
  const pane = Array.from(document.querySelectorAll('.el-tab-pane'))
    .find((p) => p.offsetParent !== null)
  if (!pane) return { rows: '无激活页签' }
  const tr = pane.querySelector('.el-table__body tr')
  return { rows: tr ? tr.innerText.replace(/\n+/g, ' | ').slice(0, 120) : '无数据' }
})

const clickInPane = (page) => page.evaluate(() => {
  const pane = Array.from(document.querySelectorAll('.el-tab-pane'))
    .find((p) => p.offsetParent !== null)
  if (!pane) return ''
  const b = Array.from(pane.querySelectorAll('button'))
    .find((x) => ['停用', '启用'].includes((x.innerText || '').trim()))
  if (!b) return ''
  const t = b.innerText.trim()
  b.click()
  return t
})

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))
  page.on('console', (m) => { if (m.type() === 'error') console.log('控制台:', m.text().slice(0, 160)) })

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

  await page.goto(BASE + '/#/sys/dict', { waitUntil: 'networkidle2' })
  await sleep(3000)
  console.log('初始:', JSON.stringify(await paneInfo(page)))
  const a = await clickInPane(page); await sleep(1800)
  console.log('点击:', a, '→', JSON.stringify(await paneInfo(page)))
  const b = await clickInPane(page); await sleep(1800)
  console.log('回切:', b, '→', JSON.stringify(await paneInfo(page)))
  await browser.close()
})()
