/** 诊断：租户账号的权限与菜单装配 */
const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE, headless: 'new', args: ['--no-sandbox'],
    defaultViewport: { width: 1400, height: 1000 }
  })
  const p = await b.newPage()
  const logs = []
  p.on('console', (m) => logs.push(m.text().slice(0, 200)))
  await p.evaluateOnNewDocument(() => localStorage.setItem('bp.ui.style', 'classic'))
  await p.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
  await sleep(1200)
  await p.evaluate(() => {
    const el = document.querySelectorAll('input')
    const s = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
    }
    s(0, '350600'); s(1, 'test_tenant'); s(2, 'Test@1234')
  })
  await p.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((v) => /登\s*录/.test(v.innerText || ''))
    x && x.click()
  })
  await sleep(5000)

  const info = await p.evaluate(() => {
    const raw = localStorage.getItem('bp_perms') || ''
    const all = Array.from(document.querySelectorAll('.el-menu-item, .el-sub-menu__title'))
      .map((e) => (e.textContent || '').trim())
    return { permCount: raw ? raw.split(',').length : 0, permSample: raw.slice(0, 200), menu: all }
  })
  console.log('本地权限样例:', info.permSample)
  console.log('菜单项:', info.menu.join(' | '))

  // 直接访问账单页，看是否被守卫拦截
  await p.evaluate(() => { window.location.hash = '#/bills' })
  await sleep(2500)
  const after = await p.evaluate(() => ({
    hash: window.location.hash,
    title: (document.querySelector('h3')?.innerText || '').slice(0, 40)
  }))
  console.log('访问 /#/bills 后:', JSON.stringify(after))
  await b.close()
})()
