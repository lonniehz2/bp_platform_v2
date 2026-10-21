/**
 * 探测登录后页面的真实 DOM 结构：导航容器、菜单元素、表格、卡片
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const OUT = __dirname
const SHOT = path.join(OUT, 'shots')
if (!fs.existsSync(SHOT)) fs.mkdirSync(SHOT, { recursive: true })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1680, height: 1000 }
  })
  const page = await browser.newPage()
  const out = []
  const say = (s) => { console.log(s); out.push(s) }

  try {
    await page.goto('https://saas.yumeng.work/', { waitUntil: 'networkidle2', timeout: 90000 })
    await sleep(2500)
    await page.type('input[name="username"]', '17701311856', { delay: 30 })
    await page.type('input[name="password"]', 'a123456', { delay: 30 })
    await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button'))
        .find((x) => /登\s*录/.test(x.innerText || ''))
      b && b.click()
    })
    await sleep(7000)
    say('URL: ' + page.url())
    await page.screenshot({ path: path.join(SHOT, '10-workbench.png'), fullPage: false })

    // 1) 找侧边导航容器：包含最多「短文本可点击元素」的容器
    const navInfo = await page.evaluate(() => {
      const cands = []
      const nodes = document.querySelectorAll('div, ul, aside, nav')
      nodes.forEach((el) => {
        const cls = (el.className || '').toString()
        if (!/menu|nav|sider|sidebar|aside/i.test(cls)) return
        const items = el.querySelectorAll('a, li, div[class*=item]')
        if (items.length >= 3) {
          cands.push({
            cls: cls.slice(0, 120),
            tag: el.tagName,
            n: items.length,
            sample: Array.from(items).slice(0, 8)
              .map((x) => (x.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 20))
          })
        }
      })
      return cands.sort((a, b) => b.n - a.n).slice(0, 6)
    })
    say('\n=== 导航容器候选 ===')
    navInfo.forEach((c) => say(`  [${c.tag}] ${c.cls}\n     ${c.n} 项: ${c.sample.join(' | ')}`))

    // 2) 全页可点击短文本（可能是菜单）
    const shortTexts = await page.evaluate(() => {
      const set = new Set()
      document.querySelectorAll('a, li, span, div').forEach((el) => {
        if (el.children.length > 0) return
        const t = (el.innerText || '').trim()
        if (t && t.length <= 8 && /[\u4e00-\u9fa5]/.test(t)) set.add(t)
      })
      return Array.from(set).slice(0, 120)
    })
    say('\n=== 页面短文本（前 120）===')
    say('  ' + shortTexts.join(' / '))

    // 3) 表格结构
    const tables = await page.evaluate(() => {
      const out = []
      document.querySelectorAll('table').forEach((t, i) => {
        const th = Array.from(t.querySelectorAll('th')).map((x) => (x.innerText || '').trim())
        const rows = Array.from(t.querySelectorAll('tbody tr')).slice(0, 2).map((tr) =>
          Array.from(tr.querySelectorAll('td')).map((td) => (td.innerText || '').trim().slice(0, 26)))
        out.push({ i, th, rows })
      })
      return out
    })
    say('\n=== 表格 (' + tables.length + ' 个) ===')
    tables.forEach((t) => say(`  #${t.i} 列: ${JSON.stringify(t.th)}\n     行: ${JSON.stringify(t.rows)}`))

    // 4) 页面主要区块（卡片）
    const cards = await page.evaluate(() => {
      const out = []
      document.querySelectorAll('[class*=card], [class*=panel], [class*=box]').forEach((el) => {
        const t = (el.innerText || '').trim().replace(/\s+/g, ' ')
        if (t.length > 2 && t.length < 120) out.push((el.className || '').toString().slice(0, 50) + ' :: ' + t.slice(0, 80))
      })
      return out.slice(0, 25)
    })
    say('\n=== 卡片区块 ===')
    cards.forEach((c) => say('  ' + c))

    const bodyText = await page.evaluate(() => (document.body.innerText || '').slice(0, 4000))
    fs.writeFileSync(path.join(OUT, 'workbench-text.txt'), bodyText, 'utf8')
    fs.writeFileSync(path.join(OUT, 'probe.log'), out.join('\n'), 'utf8')
    say('\n已存 workbench-text.txt / probe.log')
  } catch (e) {
    say('ERROR: ' + e.message)
  } finally {
    await browser.close()
  }
})()
