/**
 * 深度抓取：完整菜单树 + 关键业务页（房源/合同/财务）的筛选、表格、行操作 + 截图
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const OUT = __dirname
const SHOT = path.join(OUT, 'shots')
if (!fs.existsSync(SHOT)) fs.mkdirSync(SHOT, { recursive: true })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const report = {}
const say = (s) => console.log(s)

async function login(page) {
  await page.goto('https://saas.yumeng.work/', { waitUntil: 'networkidle2', timeout: 90000 })
  await sleep(2500)
  await page.type('input[name="username"]', '17701311856', { delay: 25 })
  await page.type('input[name="password"]', 'a123456', { delay: 25 })
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await sleep(7000)
}

/** 抓当前页的筛选控件、表格列、行内操作按钮 */
async function capturePage(page) {
  return page.evaluate(() => {
    const norm = (s) => (s || '').trim().replace(/\s+/g, ' ')
    // 筛选区：输入框 placeholder / select 文本
    const filters = []
    document.querySelectorAll('input[placeholder]').forEach((el) => {
      filters.push('输入:' + el.placeholder.slice(0, 16))
    })
    document.querySelectorAll('.ant-select-selection-placeholder, .ant-select-selection-selected-value')
      .forEach((el) => { const t = norm(el.innerText); if (t) filters.push('选择:' + t.slice(0, 16)) })
    // 按钮
    const btns = Array.from(document.querySelectorAll('button'))
      .map((b) => norm(b.innerText)).filter((t) => t && t.length <= 12)
    // 表格
    const tables = []
    document.querySelectorAll('table').forEach((t) => {
      const th = Array.from(t.querySelectorAll('th')).map((x) => norm(x.innerText))
      const rows = Array.from(t.querySelectorAll('tbody tr')).slice(0, 2)
        .map((tr) => Array.from(tr.querySelectorAll('td')).map((td) => norm(td.innerText).slice(0, 22)))
      if (th.length) tables.push({ th, rows })
    })
    // 标签页
    const tabs = Array.from(document.querySelectorAll('.ant-tabs-tab'))
      .map((x) => norm(x.innerText)).filter(Boolean)
    return {
      url: location.hash, filters: [...new Set(filters)].slice(0, 24),
      buttons: [...new Set(btns)].slice(0, 24), tabs, tables,
      text: norm(document.body.innerText).slice(0, 600)
    }
  })
}

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1680, height: 1000 }
  })
  const page = await browser.newPage()
  try {
    await login(page)

    // ---------- 1. 一级导航 + 更多菜单（完整） ----------
    const nav = await page.evaluate(() => {
      const top = Array.from(document.querySelectorAll('.sidebarList a, .sidebarList div'))
        .map((x) => (x.innerText || '').trim()).filter((t) => t && t.length <= 8)
      const more = Array.from(document.querySelectorAll('.moreMenuList a, .moreMenuList li, .moreMenuList div'))
        .map((x) => (x.innerText || '').trim()).filter((t) => t && t.length <= 10)
      return { top: [...new Set(top)], more: [...new Set(more)] }
    })
    report.nav = nav
    say('一级导航：' + nav.top.join(' / '))
    say('更多菜单（' + nav.more.length + '）：' + nav.more.join(' / '))

    // ---------- 2. 驾驶舱结构 ----------
    report.dashboard = await capturePage(page)
    await page.screenshot({ path: path.join(SHOT, '20-dashboard.png') })

    // ---------- 3. 遍历关键一级导航 ----------
    const targets = ['房源', '合同', '财务', '会员', '管理后台', '线索']
    report.pages = {}
    for (const t of targets) {
      const ok = await page.evaluate((label) => {
        const el = Array.from(document.querySelectorAll('.sidebarList *'))
          .find((x) => (x.innerText || '').trim() === label)
        if (el) { el.click(); return true }
        return false
      }, t)
      if (!ok) { say(`跳过 ${t}`); continue }
      await sleep(3500)
      const info = await capturePage(page)
      report.pages[t] = info
      say(`\n■ ${t}  ${info.url}`)
      say('  筛选: ' + info.filters.slice(0, 10).join(' | '))
      say('  按钮: ' + info.buttons.slice(0, 12).join(' | '))
      if (info.tables[0]) {
        say('  列: ' + info.tables[0].th.join(' | '))
        say('  行: ' + JSON.stringify(info.tables[0].rows[0] || []).slice(0, 200))
      }
      await page.screenshot({
        path: path.join(SHOT, `3x-${t}.png`)
      })
    }

    fs.writeFileSync(path.join(OUT, 'reference.json'),
      JSON.stringify(report, null, 1), 'utf8')
    say('\n已保存 reference.json')
  } catch (e) {
    say('ERROR: ' + e.message)
    try { await page.screenshot({ path: path.join(SHOT, '99-error.png') }) } catch (_) {}
  } finally {
    await browser.close()
  }
})()
