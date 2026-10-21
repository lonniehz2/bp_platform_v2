const puppeteer = require('puppeteer-core')
const sleep = ms => new Promise(r => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', headless: 'new', args: ['--no-sandbox'], defaultViewport: { width: 1500, height: 900 } })
  const p = await b.newPage()
  await p.goto('http://192.168.31.11:8080/', { waitUntil: 'networkidle2' })
  await sleep(1200)
  await p.evaluate(() => { const e = document.querySelectorAll('input'); const s = (i, v) => { e[i].value = v; e[i].dispatchEvent(new Event('input', { bubbles: true })) }; s(0, '350600'); s(1, 'admin'); s(2, 'admin123') })
  await p.evaluate(() => { const x = Array.from(document.querySelectorAll('button')).find(y => /登\s*录/.test(y.innerText)); x && x.click() })
  for (let i = 0; i < 30; i++) { await sleep(400); if (await p.evaluate(() => !!document.querySelector('.rail,.el-menu'))) break }
  await p.goto('http://192.168.31.11:8080/#/persons', { waitUntil: 'domcontentloaded' }); await sleep(2000)
  const btns = await p.evaluate(() => Array.from(document.querySelectorAll('button')).map(x => x.innerText.trim()).filter(Boolean).slice(0, 20))
  console.log('列表页按钮:', JSON.stringify(btns))
  await p.evaluate(() => { const x = Array.from(document.querySelectorAll('button')).find(y => (y.innerText||'').replace(/\s/g,'') === '新增人员'); x && x.click() })
  await sleep(1200)
  const dlg = await p.evaluate(() => {
    const d = document.querySelector('.el-dialog')
    if (!d) return { found: false }
    return {
      found: true,
      title: (d.querySelector('.el-dialog__title') || {}).innerText,
      inputs: Array.from(d.querySelectorAll('input')).map(x => x.placeholder || x.type),
      selects: d.querySelectorAll('.el-select').length,
      buttons: Array.from(d.querySelectorAll('button')).map(x => x.innerText.trim())
    }
  })
  console.log('弹窗:', JSON.stringify(dlg, null, 1))
  await b.close()
})()
