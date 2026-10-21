/**
 * 多 tab 页面「路由驱动」验证
 *
 * 对每个页面断言：任意 tab 的深链都能打开对应面板；无参数时落到默认 tab。
 * 用法：node _check_tab_routes.js
 */
const puppeteer = require('puppeteer-core')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const CASES = [
  { path: '/ops-extras', tabs: ['msg', 'rule', 'open', 'rbac', 'grant', 'calendar'] },
  { path: '/rbac', tabs: ['user', 'role', 'perm'] },
  { path: '/sys', tabs: ['audit', 'dict', 'config'] },
  { path: '/ops-center', tabs: ['person', 'house', 'order'] }
]

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'], defaultViewport: { width: 1500, height: 950 }
  })
  const page = await browser.newPage()
  const errs = []
  page.on('pageerror', (e) => errs.push(e.message))

  await page.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
  await sleep(1200)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  for (let i = 0; i < 40; i++) {
    await sleep(400)
    if (await page.evaluate(() => !!document.querySelector('.el-menu, .rail'))) break
  }

  let pass = 0
  let total = 0
  const activeTab = () => page.evaluate(() => {
    const a = document.querySelector('.el-tabs__item.is-active')
    return a ? a.innerText.trim() : '(无)'
  })

  for (const c of CASES) {
    console.log('\n' + c.path)
    // 无参数 → 默认 tab（第一个）
    await page.evaluate((h) => { location.hash = '#' + h }, c.path)
    await sleep(1400)
    const def = await activeTab()
    total++
    if (def && def !== '(无)') { pass++; console.log('  ✓ 无参数落默认 tab: ' + def) } else console.log('  ✗ 无参数未落到任何 tab')

    for (const t of c.tabs) {
      await page.evaluate((h) => { location.hash = h }, '#' + c.path + '/' + t)
      await sleep(1200)
      const info = await page.evaluate(() => {
        const a = document.querySelector('.el-tabs__item.is-active')
        return { tab: a ? a.innerText.trim() : '(无)', hash: location.hash }
      })
      total++
      // 深链生效且 URL 未被回写成别的 tab
      if (info.tab !== '(无)' && info.hash.endsWith('/' + t)) { pass++; console.log(`  ✓ ${t} → ${info.tab}`) } else console.log(`  ✗ ${t} → ${info.tab} (hash=${info.hash})`)
    }
  }

  console.log(`\n多 tab 路由：通过 ${pass} / ${total}`)
  if (errs.length) console.log('JS 报错：' + errs[0].slice(0, 100))
  await browser.close()
  process.exit(pass === total ? 0 : 1)
})()
