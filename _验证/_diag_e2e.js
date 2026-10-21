/**
 * 诊断：合同弹窗内控件结构 + 日期控件能否被程序化输入
 * 用法：node _diag_e2e.js
 */
const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = process.argv[2] || 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'], defaultViewport: { width: 1600, height: 950 }
  })
  const page = await browser.newPage()
  page.on('pageerror', (e) => console.log('[pageerror]', e.message.slice(0, 150)))
  page.on('console', (m) => { if (m.type() === 'error') console.log('[console.error]', m.text().slice(0, 150)) })

  await page.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
  await sleep(1000)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  for (let i = 0; i < 30; i++) { await sleep(400); if (await page.evaluate(() => !!document.querySelector('.el-menu'))) break }

  const token = await page.evaluate(() => localStorage.getItem('bp_token'))
  const api = (p) => page.evaluate(async (url, t) => {
    const r = await fetch(url, { headers: { 'X-Tenant-Id': '350600', Authorization: 'Bearer ' + t } })
    return r.json()
  }, BASE + p, token || '')

  // ---- 1. 人员列表：真实分页与排序 ----
  const persons = await api('/api/v1/persons?pageNum=1&pageSize=20')
  const pd = persons.data || {}
  console.log('\n[人员] total=', pd.total, 'rows=', (pd.rows || []).length)
  console.log('[人员] 首页 id 序列：', (pd.rows || []).map((r) => r.id).slice(0, 6).join(','))
  console.log('[人员] 末位 id：', (pd.rows || []).slice(-2).map((r) => r.id).join(','))

  // ---- 2. 合同列表与房源/人员 ----
  const houses = await api('/api/v1/houses?pageNum=1&pageSize=5&houseStatus=VACANT')
  console.log('\n[房源] VACANT total=', (houses.data || {}).total)

  // ---- 3. DOM 行数（确认 fixed 列是否重复渲染）----
  await page.goto(BASE + '/#/persons', { waitUntil: 'domcontentloaded' })
  await sleep(2500)
  const dom = await page.evaluate(() => ({
    mainRows: document.querySelectorAll('.el-table__body-wrapper .el-table__body tbody tr').length,
    allRows: document.querySelectorAll('.el-table__body tbody tr').length,
    hasFixedWrap: !!document.querySelector('.el-table__fixed-right, .el-table__fixed'),
    pagination: (document.querySelector('.el-pagination') || {}).innerText || '',
    firstRowText: ((document.querySelector('.el-table__body tbody tr') || {}).innerText || '').replace(/\s+/g, ' ').slice(0, 80),
    toolbarInputs: Array.from(document.querySelectorAll('.toolbar input')).map((i) => i.placeholder)
  }))
  console.log('\n[DOM 人员页]', JSON.stringify(dom, null, 1))

  // ---- 4. 合同弹窗控件清单 ----
  await page.goto(BASE + '/#/contracts', { waitUntil: 'domcontentloaded' })
  await sleep(2500)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => (x.innerText || '').replace(/\s/g, '') === '新建合同')
    b && b.click()
  })
  await sleep(900)
  const dlg = await page.evaluate(() => {
    const d = document.querySelector('.el-dialog')
    if (!d) return { err: 'no-dialog' }
    return {
      inputs: Array.from(d.querySelectorAll('input')).map((i, idx) => ({
        idx, tid: i.getAttribute('data-testid') || '',
        ph: i.placeholder || '', type: i.getAttribute('type') || '',
        cls: (i.className || '').slice(0, 40)
      }))
    }
  })
  console.log('\n[合同弹窗输入框]', JSON.stringify(dlg, null, 1))

  // ---- 5. 试填日期：真实键盘 ----
  const dt = await page.evaluate(() => {
    const d = document.querySelector('.el-dialog')
    return !!(d && d.querySelector('[data-testid="c-lease-start"] input'))
  })
  console.log('\n[日期] 包裹 div 内命中 input：', dt)
  if (dt) {
    const sel = '.el-dialog [data-testid="c-lease-start"] input'
    await page.click(sel).catch(() => {})
    await page.type(sel, '2026-11-01', { delay: 30 }).catch((e) => console.log('[type err]', e.message))
    await page.keyboard.press('Enter')
    await sleep(600)
    const v = await page.evaluate(() => {
      const i = document.querySelector('.el-dialog [data-testid="c-lease-start"] input')
      return { value: i ? i.value : null, panelOpen: !!document.querySelector('.el-picker-panel:not([style*="display: none"])') }
    })
    console.log('[日期] 键入后 input.value =', JSON.stringify(v))
  }

  // ---- 6. 弹窗所有按钮 ----
  const btns = await page.evaluate(() => {
    const d = document.querySelector('.el-dialog')
    return d ? Array.from(d.querySelectorAll('button')).map((b) => (b.innerText || '').trim()) : []
  })
  console.log('\n[合同弹窗按钮]', JSON.stringify(btns))

  await browser.close()
})()
