const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE, headless: 'new', args: ['--no-sandbox'],
    defaultViewport: { width: 1500, height: 1000 }
  })
  const p = await b.newPage()
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
  await p.evaluate(() => { window.location.hash = '#/workorders' })
  await sleep(2500)
  const opened = await p.evaluate(() => {
    const btn = document.querySelector('[data-testid="inspection-plans"]')
      || Array.from(document.querySelectorAll('button')).find((b) => (b.innerText || '').includes('巡检计划'))
    if (!btn) return false
    btn.click()
    return true
  })
  await sleep(2000)
  const info = await p.evaluate(() => {
    const dlg = document.querySelector('.el-dialog')
    if (!dlg) return { dialog: false }
    const rows = Array.from(dlg.querySelectorAll('.el-table tbody tr')).map((tr) =>
      Array.from(tr.querySelectorAll('td')).map((td) => (td.innerText || '').trim()).join(' | '))
    const btns = Array.from(dlg.querySelectorAll('button')).map((b) => (b.innerText || '').trim())
    return { dialog: true, rows, btns }
  })
  console.log('打开巡检计划:', opened)
  console.log('弹窗按钮:', (info.btns || []).join(' / '))
  console.log('计划行数:', (info.rows || []).length)
  ;(info.rows || []).slice(0, 3).forEach((r) => console.log('  ' + r))
  await p.screenshot({ path: __dirname + '/inspection-plan.png' })
  await b.close()
})()
