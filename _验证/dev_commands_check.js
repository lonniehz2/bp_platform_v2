// 设备指令页验证
const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 180)))
  page.on('console', (m) => { if (m.type() === 'error') console.log('控制台:', m.text().slice(0, 180)) })

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2200)

  await page.evaluate(() => { location.hash = '#/dev-commands' })
  await sleep(3500)
  const info = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 120))
    return { title: document.querySelector('h3')?.innerText, count: rows.length, rows: rows.slice(0, 3),
      buttons: Array.from(document.querySelectorAll('.toolbar button')).map((b) => b.innerText.trim()) }
  })
  console.log('页面:', info.title, '| 行数:', info.count)
  info.rows.forEach((r) => console.log('  ', r))
  console.log('按钮:', info.buttons.join(' | '))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'dev-commands.png') })

  // 打开新建弹窗
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建指令'))
    if (b) b.click()
  })
  await sleep(1200)
  const dlg = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return { labels: Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim()) }
  })
  console.log('新建弹窗:', JSON.stringify(dlg))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'dev-commands-create.png') })
  await browser.close()
})()
