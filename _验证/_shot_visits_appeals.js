const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const TARGETS = [['#/visits', 'visits'], ['#/appeals', 'appeals']]

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
  for (const [hash, name] of TARGETS) {
    await p.evaluate((h) => { window.location.hash = h }, hash)
    await sleep(2200)
    const info = await p.evaluate(() => {
      const tr = document.querySelector('.el-table tbody tr')
      if (!tr) return { rows: 0 }
      const cells = Array.from(tr.querySelectorAll('td'))
      const opCell = cells[cells.length - 1]
      const els = Array.from(opCell.querySelectorAll('button'))
      const tops = new Set(els.map((e) => Math.round(e.getBoundingClientRect().top)))
      return {
        buttons: els.map((e) => (e.innerText || '').trim()),
        lineCount: tops.size,
        opWidth: Math.round(opCell.getBoundingClientRect().width)
      }
    })
    console.log(name + ':', JSON.stringify(info))
    await p.screenshot({ path: __dirname + '/' + name + '-op.png' })
  }
  await b.close()
})()
