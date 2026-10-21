/**
 * UI 自动化冒烟测试
 *
 * 用本机 Edge 驱动真实浏览器，逐个访问全部业务页面，检查：
 *   ① 控制台报错（JS 异常 / Vue warning）
 *   ② 页面级异常（pageerror、未捕获 Promise）
 *   ③ 接口请求失败（4xx/5xx）
 *   ④ 表格是否有数据 / 是否命中空态
 *   ⑤ 保存截图，便于人工复核
 *
 * 用法：node ui_smoke.js <routesJson> <outDir> [baseUrl]
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const routesFile = process.argv[2]
const outDir = process.argv[3] || __dirname
const BASE = process.argv[4] || 'http://192.168.31.11:8080'

const routes = JSON.parse(fs.readFileSync(routesFile, 'utf8'))
const shots = path.join(outDir, 'ui-shots')
if (!fs.existsSync(shots)) fs.mkdirSync(shots, { recursive: true })

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const report = { base: BASE, total: 0, ok: 0, failed: [], warnings: [], pages: [] }

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1600, height: 950 }
  })
  const page = await browser.newPage()

  let errors = []
  let apiFails = []
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message))
  page.on('console', (m) => {
    if (m.type() === 'error') {
      const t = m.text()
      // 忽略浏览器网络噪声
      if (/favicon|ERR_|Failed to load resource/i.test(t)) return
      errors.push('console: ' + t.slice(0, 200))
    }
  })
  page.on('response', (r) => {
    const u = r.url()
    if (u.includes('/api/') && r.status() >= 400) {
      apiFails.push(`${r.status()} ${u.replace(BASE, '')}`)
    }
  })

  try {
    // ---------- 登录 ----------
    await page.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
    await sleep(1200)
        const n = await page.evaluate(() => document.querySelectorAll('input').length)
    if (n < 3) throw new Error('登录表单结构不符，输入框数=' + n)
    // 直接赋值 + 派发 input 事件，避免键盘输入重复与焦点丢失
    await page.evaluate(() => {
      const el = document.querySelectorAll('input')
      const set = (i, v) => {
        el[i].focus()
        el[i].value = v
        el[i].dispatchEvent(new Event('input', { bubbles: true }))
        el[i].dispatchEvent(new Event('change', { bubbles: true }))
        el[i].blur()
      }
      set(0, '350600')
      set(1, 'admin')
      set(2, 'admin123')
    })
    await sleep(300)
    await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button'))
        .find((x) => /登\s*录/.test(x.innerText || ''))
      b && b.click()
    })
    let loggedIn = false
    for (let i = 0; i < 30; i++) {
      await sleep(500)
      loggedIn = await page.evaluate(
        () => !!document.querySelector('.rail, .el-menu, .aside'))
      if (loggedIn) break
    }
    report.loggedIn = loggedIn
    console.log('登录：' + (loggedIn ? '成功' : '失败'))
    if (!loggedIn) {
      await page.screenshot({ path: path.join(shots, '00-login-fail.png') })
      report.failed.push({ path: '/login', reason: '登录失败' })
      fs.writeFileSync(path.join(outDir, 'ui-smoke.json'),
        JSON.stringify(report, null, 1), 'utf8')
      await browser.close()
      process.exit(1)
    }

    // ---------- 逐页检查 ----------
    for (const r of routes) {
      errors = []
      apiFails = []
      const url = BASE + '/#' + r.path
      let rows = 0
      let emptyText = ''
      let hasErrorMsg = false
      try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 })
        await sleep(r.wait || 1800)
        const info = await page.evaluate(() => {
          const trs = document.querySelectorAll('.el-table__body tbody tr')
          const empt = document.querySelector('.el-empty__description innerText, .el-empty__description, .el-table__empty-text')
          const err = document.querySelector('.el-message--error')
          return {
            rows: trs.length,
            empty: (document.querySelector('.el-table__empty-text')?.innerText
              || document.querySelector('.el-empty__description')?.innerText || '').trim(),
            hasError: !!err,
            title: (document.querySelector('.bp-page-head h2, .toolbar h3, h2')?.innerText || '').trim()
          }
        })
        rows = info.rows
        emptyText = info.empty
        hasErrorMsg = info.hasError
        await page.screenshot({
          path: path.join(shots, r.path.replace(/\//g, '_').slice(1) + '.png')
        })
      } catch (e) {
        errors.push('导航失败: ' + e.message)
      }

      const fail = []
      if (errors.length) fail.push(...errors.slice(0, 3))
      if (apiFails.length) fail.push('接口失败: ' + apiFails.slice(0, 3).join('; '))
      if (hasErrorMsg) fail.push('页面弹出错误提示')

      const rec = {
        path: r.path, title: r.title, rows, empty: emptyText,
        errors: errors.length, apiFails: apiFails.length, fail
      }
      report.pages.push(rec)
      report.total++
      if (fail.length) {
        report.failed.push(rec)
        console.log(`  ✗ ${r.path.padEnd(22)} ${r.title}  ${fail[0].slice(0, 80)}`)
      } else {
        report.ok++
        const note = rows > 0 ? `${rows} 行` : (emptyText ? `空:${emptyText.slice(0, 12)}` : '无表格')
        console.log(`  ✓ ${r.path.padEnd(22)} ${r.title}  ${note}`)
      }
    }
  } catch (e) {
    console.log('FATAL: ' + e.message)
    report.fatal = e.message
  } finally {
    fs.writeFileSync(path.join(outDir, 'ui-smoke.json'),
      JSON.stringify(report, null, 1), 'utf8')
    await browser.close()
  }

  console.log(`\n结果：通过 ${report.ok} / ${report.total}，失败 ${report.failed.length}`)
  process.exit(report.failed.length ? 1 : 0)
})()
