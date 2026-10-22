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
  p.on('console', (m) => logs.push(m.type() + ': ' + m.text().slice(0, 160)))
  p.on('requestfailed', (r) => logs.push('REQFAIL ' + r.url().slice(0, 120)))
  p.on('response', async (r) => {
    const u = r.url()
    if (u.includes('/house-calendar') || u.includes('/houses?')) {
      logs.push('RESP ' + r.status() + ' ' + u.replace('http://192.168.31.11:8080/api/v1', ''))
    }
  })

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
  await p.evaluate(() => { window.location.hash = '#/house-calendar' })
  await sleep(4000)

  const info = await p.evaluate(() => ({
    houseIdInput: Array.from(document.querySelectorAll('input')).map((i) => i.value).filter(Boolean),
    rowCount: document.querySelectorAll('.el-table tbody tr').length,
    empty: !!document.querySelector('.el-table__empty-text'),
    emptyText: document.querySelector('.el-table__empty-text')?.textContent?.trim() || ''
  }))
  console.log('页面状态:', JSON.stringify(info, null, 1))
  console.log('--- 控制台/网络 ---')
  logs.slice(-18).forEach((l) => console.log(l))
  await p.screenshot({ path: __dirname + '/calendar-debug.png' })
  await b.close()
})()
