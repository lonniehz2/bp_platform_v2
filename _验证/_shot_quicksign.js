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
  await p.evaluate(() => { window.location.hash = '#/contracts' })
  await sleep(2500)
  // 点「快捷签约」
  const clicked = await p.evaluate(() => {
    const btn = document.querySelector('[data-testid="quick-sign"]')
      || Array.from(document.querySelectorAll('button')).find((b) => (b.innerText || '').includes('快捷签约'))
    if (!btn) return false
    btn.click()
    return true
  })
  await sleep(2000)
  const info = await p.evaluate(() => {
    const dlg = document.querySelector('.el-dialog')
    if (!dlg) return { dialog: false }
    const items = Array.from(dlg.querySelectorAll('.el-form-item')).map((it) => {
      const label = (it.querySelector('.el-form-item__label')?.innerText || '').trim()
      const inputs = Array.from(it.querySelectorAll('input')).map((i) => i.placeholder || '(无占位)')
      const selects = it.querySelectorAll('.el-select').length
      return { label, inputs, selects }
    })
    return { dialog: true, items }
  })
  console.log('点击快捷签约:', clicked)
  console.log(JSON.stringify(info, null, 1).slice(0, 1200))
  await p.screenshot({ path: __dirname + '/quicksign-dialog.png' })
  await b.close()
})()
