/**
 * 侧边栏子菜单验证
 *
 * 断言：
 *   ① 四个多 tab 页面的 tab 项出现在侧边栏（不再只有父级入口）
 *   ② 点击子菜单项能跳到对应路由并激活正确 tab
 *
 * 用法：node _check_menu_tabs.js
 */
const puppeteer = require('puppeteer-core')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const EXPECT = {
  '告警规则': '/ops-extras/rule',
  '权限管理': '/ops-extras/rbac',
  '角色管理': '/rbac/role',
  '数据字典': '/sys/dict',
  '工单流程': '/ops-center/order'
}

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'], defaultViewport: { width: 1500, height: 950 }
  })
  const page = await browser.newPage()
  const errs = []
  page.on('pageerror', (e) => errs.push(e.message))
  // 固定用「风格1（宽侧栏）」：图标栏风格只显示当前分组，看不到全部子菜单
  await page.evaluateOnNewDocument(() => {
    try { localStorage.setItem('bp.ui.style', 'classic') } catch (e) {}
  })

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

  // 展开所有一级分组，让子项可见（宽侧栏用 el-sub-menu）
  await page.evaluate(() => {
    document.querySelectorAll('.el-sub-menu__title').forEach((t) => t.click())
  })
  await sleep(800)

  const menuTexts = await page.evaluate(() => {
    // 用 textContent：innerText 对隐藏（折叠）项返回空串，会漏判
    return Array.from(document.querySelectorAll('.el-menu-item, .el-sub-menu__title'))
      .map((x) => (x.textContent || '').trim())
  })

  let pass = 0
  let total = 0
  console.log('侧边栏菜单项数：', menuTexts.length)

  for (const [label, expectPath] of Object.entries(EXPECT)) {
    total++
    if (menuTexts.some((t) => t.includes(label))) {
      pass++
      console.log(`  ✓ 菜单含「${label}」`)
    } else {
      console.log(`  ✗ 菜单缺「${label}」`)
    }
  }

  // 点击「告警规则」，验证跳到 /ops-extras/rule 且 tab 激活
  await page.evaluate(() => {
    const it = Array.from(document.querySelectorAll('.el-menu-item'))
      .find((x) => (x.innerText || '').includes('告警规则'))
    if (it) it.click()
  })
  await sleep(1500)
  const after = await page.evaluate(() => {
    const a = document.querySelector('.el-tabs__item.is-active')
    return { hash: location.hash, tab: a ? a.innerText.trim() : '(无)' }
  })
  total++
  if (after.hash.endsWith('/rule') && after.tab === '告警规则') {
    pass++
    console.log(`  ✓ 点击「告警规则」→ ${after.hash}，激活 tab=${after.tab}`)
  } else {
    console.log(`  ✗ 点击「告警规则」→ ${after.hash}，tab=${after.tab}`)
  }

  console.log(`\n侧边栏子菜单：通过 ${pass} / ${total}`)
  if (errs.length) console.log('JS 报错：' + errs[0].slice(0, 100))
  await browser.close()
  process.exit(pass === total ? 0 : 1)
})()
