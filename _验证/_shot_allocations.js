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
  await p.evaluate(() => { window.location.hash = '#/allocations' })
  await sleep(2500)
  const info = await p.evaluate(() => {
    const trs = Array.from(document.querySelectorAll('.el-table tbody tr')).slice(0, 4)
    return trs.map((tr) => {
      const cells = Array.from(tr.querySelectorAll('td'))
      const status = (cells[1]?.innerText || '').trim()
      const op = cells[cells.length - 1]
      const btns = Array.from(op.querySelectorAll('button')).map((x) => (x.innerText || '').trim())
      return { status, btns }
    })
  })
  console.log(JSON.stringify(info, null, 1))
  await p.screenshot({ path: __dirname + '/allocations-buttons.png' })
  await b.close()
})()
