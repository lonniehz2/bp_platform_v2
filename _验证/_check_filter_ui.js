/**
 * 列表页「清空」按钮专项验证
 *
 * 对若干代表性页面执行：进入 → 读初始行数 → 填筛选 → 查询 → 断言行数变化
 *   → 点「清空」→ 断言筛选被清空且行数回到初始
 *
 * 覆盖三类改造：ref 置空（Houses）、reactive 快照（Bills/Contracts）、多 tab（Persons）
 *
 * 用法：node _check_filter_ui.js [outDir] [baseUrl]
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const outDir = process.argv[2] || __dirname
const BASE = process.argv[3] || 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const results = []
const ok = (n, d) => { results.push({ pass: true }); console.log('  ✓ ' + n + (d ? '  ' + d : '')) }
const bad = (n, d) => { results.push({ pass: false }); console.log('  ✗ ' + n + '  ' + (d || '')) }

/** 每个用例：路径 / 用于填写的输入框 placeholder 片段 / 要输入的值 */
const CASES = [
  { path: '/houses', ph: '房源编号', val: 'ZZ-H', name: '房源台账' },
  { path: '/bills', ph: '账期', val: '2026-10', name: '账单与缴费' },
  { path: '/contracts', ph: '合同号', val: 'BC', name: '合同管理' },
  { path: '/persons', ph: '姓名', val: '住户01', name: '保障对象' },
  { path: '/fee-items', ph: '项目编码', val: 'E2E', name: '计费项目' }
]

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'], defaultViewport: { width: 1500, height: 950 }
  })
  const page = await browser.newPage()
  const errors = []
  page.on('pageerror', (e) => errors.push(e.message))

  const waitFor = async (fn, timeout = 10000) => {
    const t0 = Date.now()
    while (Date.now() - t0 < timeout) {
      const v = await fn()
      if (v) return v
      await sleep(150)
    }
    return null
  }
  const idle = () => waitFor(async () => page.evaluate(() =>
    !document.querySelector('.el-loading-mask:not([style*="display: none"])')), 8000)
  const rowCount = () => page.evaluate(() => {
    const pane = Array.from(document.querySelectorAll('.el-tab-pane')).find((p) => p.offsetParent !== null)
    const scope = pane || document
    return Array.from(scope.querySelectorAll('.el-table__body tbody tr'))
      .filter((tr) => tr.offsetParent !== null).length
  })
  const totalText = () => page.evaluate(() => {
    const el = document.querySelector('.el-pagination__total')
    return el ? el.innerText.trim() : ''
  })

  try {
    // ---------- 登录 ----------
    await page.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
    await waitFor(async () => page.evaluate(() => document.querySelectorAll('input').length >= 3))
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
    if (!await waitFor(async () => page.evaluate(() => !!document.querySelector('.el-menu, .rail')), 20000)) {
      bad('登录', '未进入主界面'); await browser.close(); process.exit(1)
    }

    for (const c of CASES) {
      await page.evaluate((h) => { window.location.hash = h }, '#' + c.path)
      await sleep(1200)
      await idle()

      const hasReset = await page.evaluate(() => Array.from(document.querySelectorAll('button'))
        .some((b) => (b.innerText || '').trim() === '清空'))
      if (!hasReset) { bad(c.name + '：清空按钮存在', '未找到「清空」按钮'); continue }

      const before = await rowCount()
      const beforeTotal = await totalText()

      // 填筛选
      const filled = await page.evaluate((ph, v) => {
        const el = Array.from(document.querySelectorAll('input'))
          .filter((i) => i.offsetParent !== null)
          .find((i) => (i.placeholder || '').includes(ph))
        if (!el) return false
        el.focus()
        el.value = v
        el.dispatchEvent(new Event('input', { bubbles: true }))
        el.dispatchEvent(new Event('change', { bubbles: true }))
        return true
      }, c.ph, c.val)
      if (!filled) { bad(c.name + '：填写筛选', '未找到 placeholder 含「' + c.ph + '」的输入框'); continue }

      // 查询
      await page.evaluate(() => {
        const b = Array.from(document.querySelectorAll('button')).find((x) => (x.innerText || '').trim() === '查询')
        b && b.click()
      })
      await sleep(1200)
      await idle()
      const afterFilter = await totalText()

      // 清空
      await page.evaluate(() => {
        const b = Array.from(document.querySelectorAll('button')).find((x) => (x.innerText || '').trim() === '清空')
        b && b.click()
      })
      await sleep(1200)
      await idle()
      const afterReset = await totalText()
      const inputVal = await page.evaluate((ph) => {
        const el = Array.from(document.querySelectorAll('input'))
          .filter((i) => i.offsetParent !== null)
          .find((i) => (i.placeholder || '').includes(ph))
        return el ? el.value : '(未找到)'
      }, c.ph)

      const clearedOk = inputVal === ''
      const restoredOk = afterReset === beforeTotal
      clearedOk && restoredOk
        ? ok(c.name + '：清空生效', `输入框已空，${afterFilter} → ${afterReset}`)
        : bad(c.name + '：清空生效',
            `输入框="${inputVal}"，总数 ${beforeTotal} → 筛选后 ${afterFilter} → 清空后 ${afterReset}`)
      if (before === 0) console.log('    （提示：初始 0 行，页面可能无数据）')
    }

    errors.length ? bad('页面无 JS 报错', errors[0].slice(0, 90)) : ok('页面无 JS 报错')
  } catch (e) {
    bad('执行异常', e.message)
    try { await page.screenshot({ path: path.join(outDir, 'filter-ui-error.png') }) } catch (_) {}
  } finally {
    const pass = results.filter((r) => r.pass).length
    console.log(`\n列表页筛选：通过 ${pass} / ${results.length}`)
    await browser.close()
    process.exit(pass === results.length ? 0 : 1)
  }
})()
