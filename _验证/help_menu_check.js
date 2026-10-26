/**
 * 验证「使用帮助」入口：顶部图标 → 帮助页；目录跳转与搜索。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForSelector('.stat-card, .el-table__body tr', { timeout: 30000 })
  await sleep(2500)

  // 顶部帮助按钮
  const clicked = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('.header button'))
      .find((b) => b.querySelector('svg') && b.innerText.trim() === '')
    // 顶部有几个图标按钮，帮助是带 el-tooltip 的那个：按顺序取倒数第二个（帮助在退出前）
    const btns = Array.from(document.querySelectorAll('.header button'))
    const target = btns[btns.length - 2] || btn
    if (target) { target.click(); return true }
    return false
  })
  await sleep(2500)
  console.log('点击帮助:', clicked, '当前路由:', await page.evaluate(() => location.hash))

  const info = await page.evaluate(() => {
    const toc = Array.from(document.querySelectorAll('.toc-item')).map((x) => x.innerText.trim())
    const h2 = Array.from(document.querySelectorAll('.help-body h2')).map((x) => x.innerText.trim())
    const tables = document.querySelectorAll('.help-body .el-table').length
    return { tocCount: toc.length, firstToc: toc.slice(0, 3), h2Count: h2.length, tables }
  })
  console.log('目录:', info.tocCount, info.firstToc.join(' / '))
  console.log('章节数:', info.h2Count, ' 表格数:', info.tables)
  await page.screenshot({ path: path.join(__dirname, '_shots', 'help-page.png') })

  // 目录跳转
  const jumped = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.toc-item'))
    const t = items.find((x) => x.innerText.includes('账务收费'))
    if (!t) return false
    t.click()
    return true
  })
  await sleep(1200)
  const scrolled = await page.evaluate(() => {
    const el = document.querySelector('.help-body')
    return el ? el.scrollTop : -1
  })
  console.log('点击「账务收费」:', jumped, ' 内容区滚动:', scrolled)

  // 搜索
  await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('.toolbar input'))[0]
    if (!inp) return
    inp.focus(); inp.value = '核销'
    inp.dispatchEvent(new Event('input', { bubbles: true }))
  })
  await sleep(1200)
  const searched = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.help-body h2')).map((x) => x.innerText.trim()))
  console.log('搜索「核销」命中章节:', searched.join(' / ') || '无')
  await page.screenshot({ path: path.join(__dirname, '_shots', 'help-search.png') })

  await browser.close()
})()
