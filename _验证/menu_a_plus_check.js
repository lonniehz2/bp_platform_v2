/**
 * 验证 A+ 菜单：9 分组、分区标题、角标、说明、禁用态、帮助深链。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function login(page, user = 'admin', pwd = 'admin123') {
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
  await page.evaluate((u, p) => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600'); set(1, u); set(2, p)
  }, user, pwd)
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForSelector('.rail, .el-menu, .stat-card, .el-table__body tr', { timeout: 30000 })
  await sleep(2600)
}

const menuSnapshot = (page) => page.evaluate(() => {
  const groups = Array.from(document.querySelectorAll('.rail-item span')).map((x) => x.innerText.trim())
  const panel = Array.from(document.querySelectorAll('.panel-menu .el-menu-item'))
    .map((x) => ({
      text: x.innerText.replace(/\s+/g, ' ').trim(),
      disabled: x.classList.contains('is-disabled'),
      hasBadge: !!x.querySelector('.sup, .el-badge, [class*="badge"]')
    }))
  const subs = Array.from(document.querySelectorAll('.panel-menu .sub-group')).map((x) => x.innerText.trim())
  return { groups, panel, subs }
})

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))

  await login(page)
  const first = await menuSnapshot(page)
  console.log('一级分组(' + first.groups.length + '):', first.groups.join(' / '))

  // 逐个分组点开，记录分区与禁用项
  for (const g of first.groups) {
    const clicked = await page.evaluate((name) => {
      const item = Array.from(document.querySelectorAll('.rail-item'))
        .find((x) => (x.innerText || '').trim() === name)
      if (item) { item.click(); return true }
      return false
    }, g)
    await sleep(700)
    const snap = await menuSnapshot(page)
    const dis = snap.panel.filter((x) => x.disabled).length
    const badge = snap.panel.filter((x) => x.hasBadge).length
    console.log(`${clicked ? '✔' : '✘'} ${g}: ${snap.panel.length} 项` +
      `${snap.subs.length ? ' 分区[' + snap.subs.join('|') + ']' : ''}` +
      `${badge ? ' 角标' + badge : ''}${dis ? ' 禁用' + dis : ''}`)
  }

  // 回到工作台截图
  await page.evaluate(() => {
    const item = Array.from(document.querySelectorAll('.rail-item'))
      .find((x) => (x.innerText || '').trim() === '工作台')
    if (item) item.click()
  })
  await sleep(900)
  await page.screenshot({ path: path.join(OUT, 'menu-a-plus.png') })

  // 帮助深链：在账单页点问号，应带 sec=finance
  await page.evaluate(() => { location.hash = '#/bills' })
  await sleep(2200)
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('.header button'))
    const target = btns[btns.length - 2]
    if (target) target.click()
  })
  await sleep(2000)
  console.log('帮助路由:', await page.evaluate(() => location.hash))
  const helpState = await page.evaluate(() => {
    const el = document.querySelector('.help-body')
    const h2 = Array.from(document.querySelectorAll('.help-body h2')).map((x) => x.innerText.trim())
    return { scroll: el ? el.scrollTop : -1, firstVisible: h2[0], active: document.querySelector('.toc-item.active')?.innerText.trim() }
  })
  console.log('帮助定位:', JSON.stringify(helpState))
  await page.screenshot({ path: path.join(OUT, 'menu-help-link.png') })

  // 普通角色：禁用态检查（租户账号）
  const page2 = await browser.newPage()
  await page2.setViewport({ width: 1500, height: 1000 })
  await page2.setCacheEnabled(false)
  await login(page2, 'test_tenant', 'Test@1234')
  const g2 = await page2.evaluate(() => ({
    groups: Array.from(document.querySelectorAll('.rail-item span')).map((x) => x.innerText.trim()),
    disabledLock: document.querySelectorAll('.panel-menu .mi-label .lock').length
  }))
  console.log('租户可见分组:', g2.groups.join(' / '), ' 锁图标:', g2.disabledLock)
  await page2.screenshot({ path: path.join(OUT, 'menu-tenant.png') })

  await browser.close()
})()
