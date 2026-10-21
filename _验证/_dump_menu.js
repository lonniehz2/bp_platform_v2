/** 导出当前侧边栏菜单结构，用于核对分组是否按预期重排 */
const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE, headless: 'new', args: ['--no-sandbox'],
    defaultViewport: { width: 1500, height: 1200 }
  })
  const p = await b.newPage()
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
    s(0, '350600'); s(1, 'admin'); s(2, 'admin123')
  })
  await p.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((v) => /登\s*录/.test(v.innerText || ''))
    x && x.click()
  })
  await sleep(5000)
  const dump = await p.evaluate(() => {
    const groups = []
    document.querySelectorAll('.el-sub-menu').forEach((sm) => {
      const title = (sm.querySelector('.el-sub-menu__title')?.textContent || '').trim()
      const items = Array.from(sm.querySelectorAll('.el-menu-item')).map((e) => (e.textContent || '').trim())
      groups.push({ title, items })
    })
    const flat = Array.from(document.querySelectorAll('.el-menu-item'))
      .map((e) => (e.textContent || '').trim())
    return { groups, flat }
  })
  dump.groups.forEach((g) => console.log(g.title + ' → ' + g.items.join(' / ')))
  console.log('平铺菜单项数：' + dump.flat.length)
  await b.close()
})()
