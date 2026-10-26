/**
 * 用户反馈 5 项验证：报表导出任务、规则可视化/编辑、角标。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1040 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 200)))
  page.on('console', (m) => { if (m.type() === 'error') console.log('控制台:', m.text().slice(0, 200)) })

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
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
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2600)

  // 侧边角标
  const badge = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.rail a, .rail .menu-item, .el-menu-item'))
      .filter((a) => (a.innerText || '').includes('设备告警'))
    const t = items[0] ? items[0].innerText.replace(/\s+/g, ' ') : ''
    return t
  })
  console.log('侧边「设备告警」:', badge)

  // 报表导出任务
  await page.evaluate(() => { location.hash = '#/reports' })
  await sleep(4200)
  const rep = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.page-card'))
    const taskCard = cards.find((c) => (c.querySelector('h4')?.innerText || '').includes('导出任务'))
    return taskCard ? {
      rows: taskCard.querySelectorAll('.el-table__body tr').length,
      first: (taskCard.querySelector('.el-table__body tr')?.innerText || '').replace(/\s+/g, ' ').slice(0, 140),
      hint: (taskCard.querySelector('.el-alert__title')?.innerText || '').slice(0, 80)
    } : { rows: -1 }
  })
  console.log('导出任务:', JSON.stringify(rep))
  await page.screenshot({ path: path.join(OUT, 'fb-reports.png') })

  // 规则引擎
  await page.evaluate(() => { location.hash = '#/alerts' })
  await sleep(4200)
  const rules = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.page-card'))
    const c = cards.find((x) => (x.querySelector('h4')?.innerText || '').includes('规则引擎'))
    if (!c) return { ok: false }
    const tables = c.querySelectorAll('.el-table')
    const ruleRows = tables[1] ? Array.from(tables[1].querySelectorAll('.el-table__body tr')).slice(0, 2)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 130)) : []
    return { title: c.querySelector('h4').innerText, rows: ruleRows,
      selected: (c.querySelector('.el-table__body tr.current-row')?.innerText || '').slice(0, 60) }
  })
  console.log('规则引擎:', JSON.stringify(rules).slice(0, 320))
  await page.screenshot({ path: path.join(OUT, 'fb-rules.png') })

  // 打开编辑弹窗看字段
  const dlg = await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.page-card button'))
      .find((x) => x.innerText.trim() === '编辑')
    if (!b) return '无编辑按钮'
    b.click()
    return 'clicked'
  })
  await sleep(1200)
  const form = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return {
      title: d.querySelector('.el-dialog__title')?.innerText,
      labels: Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim()).slice(0, 8),
      readouts: Array.from(d.querySelectorAll('input[readonly]')).map((x) => x.value).slice(0, 2)
    }
  })
  console.log('编辑弹窗:', JSON.stringify(form))
  await page.screenshot({ path: path.join(OUT, 'fb-rule-edit.png') })

  await browser.close()
})()
