/**
 * 资金页验证：三个页签（流水/对账单/收款确认）+ 新建对账 + 确认收款。
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
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))

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
  await sleep(2400)

  await page.evaluate(() => { location.hash = '#/cashflow' })
  await sleep(3000)

  const tabs = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-radio-button__inner'))
      .map((x) => x.innerText.trim()))
  console.log('页签:', tabs.join(' / '))

  // 对账单
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-radio-button__inner'))
      .find((x) => x.innerText.includes('对账单'))
    if (t) t.click()
  })
  await sleep(2200)
  const rec = await page.evaluate(() => {
    const rows = Array.from((Array.from(document.querySelectorAll('.el-table')).find(t=>t.offsetParent)||{querySelectorAll:()=>[]}).querySelectorAll('.el-table__body tr')).slice(0, 2)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 110))
    const vis=Array.from(document.querySelectorAll('.el-table')).find(t=>t.offsetParent); return { count: vis?vis.querySelectorAll('.el-table__body tr').length:0,
      first: rows[0] || '', btns: Array.from(document.querySelectorAll('.page-card button'))
        .map((b) => b.innerText.trim()).filter(Boolean).slice(0, 8) }
  })
  console.log('对账单:', JSON.stringify(rec).slice(0, 220))
  await page.screenshot({ path: path.join(OUT, 'fin-reconcile.png') })

  // 新建对账（渠道金额与系统不同 → 有差异）
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('新建对账'))
    if (b) b.click()
  })
  await sleep(1200)
  await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    const inputs = dlg.querySelectorAll('input')
    // 渠道金额输入框通常是最后一个 text/number 输入
    const target = Array.from(inputs).find((i) => (i.placeholder || '').includes('渠道对账单'))
    if (target) {
      target.focus()
      target.value = '1000'
      target.dispatchEvent(new Event('input', { bubbles: true }))
      target.blur()
    }
    return !!target
  })
  await sleep(500)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-dialog button'))
      .find((x) => x.innerText.trim() === '保存')
    if (b) b.click()
  })
  await sleep(2600)
  const created = await page.evaluate(() => {
    const visT=Array.from(document.querySelectorAll('.el-table')).find(t=>t.offsetParent); const rows = Array.from((visT||document).querySelectorAll('.el-table__body tr')).slice(0, 1)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 130))
    return rows[0] || ''
  })
  console.log('新建后首行:', created)
  await page.screenshot({ path: path.join(OUT, 'fin-reconcile-created.png') })

  // 收款确认
  await page.evaluate(() => {
    const t = Array.from(document.querySelectorAll('.el-radio-button__inner'))
      .find((x) => x.innerText.includes('收款确认'))
    if (t) t.click()
  })
  await sleep(2500)
  const pay = await page.evaluate(() => {
    const visP=Array.from(document.querySelectorAll('.el-table')).find(t=>t.offsetParent); const rows = Array.from((visP||document).querySelectorAll('.el-table__body tr')).slice(0, 3)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 120))
    const vis=Array.from(document.querySelectorAll('.el-table')).find(t=>t.offsetParent); return { count: vis?vis.querySelectorAll('.el-table__body tr').length:0, rows }
  })
  console.log('收款确认:', JSON.stringify(pay).slice(0, 300))
  await page.screenshot({ path: path.join(OUT, 'fin-payments.png') })

  // 确认第一笔
  const confirmed = await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-table__body button'))
      .find((x) => x.innerText.includes('确认收款'))
    if (b) { b.click(); return true }
    return false
  })
  await sleep(1200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-message-box__btns button'))
      .find((x) => x.innerText.trim() === '确定' || x.innerText.trim() === 'OK')
    if (b) b.click()
  })
  await sleep(2600)
  const after = await page.evaluate(() => {
    const rows = Array.from((Array.from(document.querySelectorAll('.el-table')).find(t=>t.offsetParent)||{querySelectorAll:()=>[]}).querySelectorAll('.el-table__body tr')).slice(0, 2)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 120))
    return { clicked: true, count: document.querySelectorAll('.el-table__body tr').length, rows }
  })
  console.log('确认后:', JSON.stringify(after).slice(0, 260))
  await page.screenshot({ path: path.join(OUT, 'fin-payment-confirmed.png') })

  await browser.close()
})()
