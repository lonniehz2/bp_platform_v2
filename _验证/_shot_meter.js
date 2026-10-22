const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE, headless: 'new', args: ['--no-sandbox'],
    defaultViewport: { width: 1500, height: 1000 }
  })
  const p = await b.newPage()
  const logs = []
  p.on('pageerror', (e) => logs.push('PAGEERROR ' + String(e).slice(0, 160)))
  p.on('response', (r) => { const u = r.url(); if (u.includes('/fin/') || u.includes('/houses')) logs.push('RESP ' + r.status() + ' ' + u.replace('http://192.168.31.11:8080/api/v1','')) })
  p.on('console', (m) => { if (m.type() === 'error') logs.push(m.text().slice(0, 120)) })
  await p.goto('http://192.168.31.11:8080/', { waitUntil: 'networkidle2', timeout: 60000 })
  await sleep(1200)
  await p.evaluate(() => {
    const el = document.querySelectorAll('input')
    const s = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
    }
    s(0, '350600'); s(1, 'admin'); s(2, 'admin123')
  })
  await p.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((v) => /登\s*录/.test(v.innerText || ''))
    x && x.click()
  })
  await sleep(4500)
  await p.evaluate(() => { window.location.hash = '#/bills' })
  await sleep(2500)
  const clicked = await p.evaluate(() => {
    const btn = document.querySelector('[data-testid="meter-reading"]')
      || Array.from(document.querySelectorAll('button')).find((b) => (b.innerText || '').includes('抄表录入'))
    if (!btn) return false
    btn.click()
    return true
  })
  await sleep(2500)
  const info = await p.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog')).find((d) => d.style.display !== 'none')
    if (!dlg) return { dialog: false }
    const rows = Array.from(dlg.querySelectorAll('.el-table tbody tr')).map((tr) =>
      Array.from(tr.querySelectorAll('td')).map((td) => (td.innerText || '').trim()).join(' | '))
    return {
      dialog: true,
      title: (dlg.querySelector('.el-dialog__title')?.innerText || '').trim(),
      labels: Array.from(dlg.querySelectorAll('.el-form-item__label')).map((l) => l.innerText.trim()),
      rows
    }
  })
  console.log('点击抄表录入:', clicked, '| 弹窗:', info.title)
  console.log('表单字段:', (info.labels || []).join(' / '))
  console.log('读数行数:', (info.rows || []).length)
  ;(info.rows || []).slice(0, 3).forEach((r) => console.log('  ' + r))
  if (logs.length) console.log('控制台错误:', logs.slice(0, 3).join(' | '))
  await p.screenshot({ path: __dirname + '/meter-reading.png' })
  await b.close()
})()
