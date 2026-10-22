/** 用指定账号登录并导出左侧菜单（验证按角色过滤） */
const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function dumpMenu(user, pass) {
  const b = await puppeteer.launch({
    executablePath: EDGE, headless: 'new', args: ['--no-sandbox'],
    defaultViewport: { width: 1400, height: 1000 }
  })
  const p = await b.newPage()
  await p.evaluateOnNewDocument(() => localStorage.setItem('bp.ui.style', 'classic'))
  await p.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
  await sleep(1200)
  await p.evaluate((u, pw) => {
    const el = document.querySelectorAll('input')
    const s = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
    }
    s(0, '350600'); s(1, u); s(2, pw)
  }, user, pass)
  await p.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((v) => /登\s*录/.test(v.innerText || ''))
    x && x.click()
  })
  await sleep(5000)
  const groups = await p.evaluate(() => {
    const out = []
    document.querySelectorAll('.el-sub-menu').forEach((sm) => {
      const t = (sm.querySelector('.el-sub-menu__title')?.textContent || '').trim()
      const items = Array.from(sm.querySelectorAll('.el-menu-item')).map((e) => (e.textContent || '').trim())
      if (items.length) out.push(t + '：' + items.join(' / '))
    })
    return out
  })
  console.log('\n=== ' + user + ' 的左侧菜单 ===')
  if (groups.length === 0) console.log('(无分组菜单)')
  groups.forEach((g) => console.log('  ' + g))
  await p.screenshot({ path: __dirname + '/' + user + '-menu.png' })
  await b.close()
}

;(async () => {
  await dumpMenu('test_tenant', 'Test@1234')
  await dumpMenu('test_finance', 'Test@1234')
})()
