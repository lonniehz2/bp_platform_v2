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
  const info = await p.evaluate(() => {
    const headers = Array.from(document.querySelectorAll('.el-table th'))
      .map((e) => (e.innerText || '').trim()).filter(Boolean)
    const btns = Array.from(document.querySelectorAll('.el-table tbody tr:first-child button'))
      .map((e) => (e.innerText || '').trim())
    return { headers, btns }
  })
  console.log('表头:', info.headers.join(' | '))
  console.log('首行按钮:', info.btns.join(' | '))
  await p.screenshot({ path: __dirname + '/contracts-table.png' })
  await b.close()
})()
