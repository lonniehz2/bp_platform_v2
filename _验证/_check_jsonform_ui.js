/**
 * JSON 编辑器 → 表单化 专项验证
 *
 * 对已改造的页面断言：
 *   ① 弹窗里不再是 JSON 文本框（没有 monospace 大 textarea）
 *   ② 必填字段控件存在（按 data-testid="f-<key>"）
 *   ③ 空表单提交被前端拦住（提示「请填写」而不是 400）
 *   ④ 填齐必填项后提交成功
 *
 * 用法：node _check_jsonform_ui.js [outDir] [baseUrl]
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

/** 已改造页面：路径 / 打开弹窗的按钮文案 / 需断言的字段 testid / 需填写的字段 */
const CASES = [
  {
    path: '/alerts', name: '告警', openBtn: '新建告警',
    tids: ['f-alertCategory', 'f-alertLevel', 'f-alertType', 'f-alertTitle'],
    fill: { 'f-alertType': 'E2E_FORM_TEST', 'f-alertTitle': '表单化验证告警' }
  },
  {
    path: '/appeals', name: '申诉', openBtn: '新建申诉',
    tids: ['f-bizType', 'f-appealType', 'f-bizId', 'f-personId', 'f-appealReason'],
    fill: { 'f-bizId': '1', 'f-personId': '1', 'f-appealReason': '表单化验证申诉理由' }
  }
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

  try {
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
      await page.evaluate((h) => { window.location.hash = '#' + h }, c.path)
      await sleep(1300)
      await waitFor(async () => page.evaluate(() =>
        !document.querySelector('.el-loading-mask:not([style*="display: none"])')))

      const opened = await page.evaluate((t) => {
        const b = Array.from(document.querySelectorAll('button'))
          .find((x) => (x.innerText || '').trim() === t)
        if (!b) return false
        b.click()
        return true
      }, c.openBtn)
      if (!opened) { bad(c.name + '：打开弹窗', '未找到按钮「' + c.openBtn + '」'); continue }
      await sleep(900)

      // ① 不应再有 JSON 大文本框
      const jsonArea = await page.evaluate(() => {
        const ds = Array.from(document.querySelectorAll('.el-dialog')).filter((d) => d.offsetParent !== null)
        const d = ds[ds.length - 1]
        if (!d) return 'no-dialog'
        const ta = Array.from(d.querySelectorAll('textarea'))
        return ta.some((t) => (t.style.fontFamily || '').includes('monospace') || t.rows >= 10)
          ? 'still-json' : 'ok'
      })
      jsonArea === 'ok'
        ? ok(c.name + '：已移除 JSON 文本框')
        : bad(c.name + '：已移除 JSON 文本框', jsonArea)

      // ② 必填字段控件都在
      const missing = await page.evaluate((tids) => {
        const ds = Array.from(document.querySelectorAll('.el-dialog')).filter((d) => d.offsetParent !== null)
        const d = ds[ds.length - 1]
        if (!d) return tids
        return tids.filter((t) => !d.querySelector('[data-testid="' + t + '"]'))
      }, c.tids)
      missing.length === 0
        ? ok(c.name + '：必填控件齐全', c.tids.length + ' 个字段')
        : bad(c.name + '：必填控件齐全', '缺：' + missing.join(','))

      // ③ 空提交被前端拦住
      const blocked = await page.evaluate(() => {
        const ds = Array.from(document.querySelectorAll('.el-dialog')).filter((d) => d.offsetParent !== null)
        const d = ds[ds.length - 1]
        const b = d && Array.from(d.querySelectorAll('button')).find((x) => (x.innerText || '').trim() === '提交')
        if (b) { b.click(); return true }
        return false
      })
      const warn = await waitFor(async () => page.evaluate(() => {
        const m = Array.from(document.querySelectorAll('.el-message'))
          .map((x) => (x.innerText || '').trim())
        return m.find((t) => t.includes('请填写')) || null
      }), 5000)
      blocked && warn
        ? ok(c.name + '：空提交被拦截', warn)
        : bad(c.name + '：空提交被拦截', '提示=' + (warn || '无'))

      // ④ 填齐后提交成功
      for (const [tid, val] of Object.entries(c.fill)) {
        await page.evaluate((t, v) => {
          const el = document.querySelector('[data-testid="' + t + '"]')
          const input = el && (el.tagName === 'INPUT' ? el : el.querySelector('input'))
          if (!input) return
          input.focus(); input.value = v
          input.dispatchEvent(new Event('input', { bubbles: true }))
          input.dispatchEvent(new Event('change', { bubbles: true }))
        }, tid, val)
      }
      const submitted = await page.evaluate(() => {
        const ds = Array.from(document.querySelectorAll('.el-dialog')).filter((d) => d.offsetParent !== null)
        const d = ds[ds.length - 1]
        const b = d && Array.from(d.querySelectorAll('button')).find((x) => (x.innerText || '').trim() === '提交')
        if (b) { b.click(); return true }
        return false
      })
      const success = await waitFor(async () => page.evaluate(() => {
        const m = Array.from(document.querySelectorAll('.el-message'))
          .map((x) => (x.innerText || '').trim())
        return m.find((t) => t.includes('成功')) || null
      }), 8000)
      submitted && success
        ? ok(c.name + '：填齐后提交成功', success)
        : bad(c.name + '：填齐后提交成功', '提示=' + (success || '无'))
    }

    errors.length ? bad('页面无 JS 报错', errors[0].slice(0, 90)) : ok('页面无 JS 报错')
  } catch (e) {
    bad('执行异常', e.message)
    try { await page.screenshot({ path: path.join(outDir, 'jsonform-error.png') }) } catch (_) {}
  } finally {
    const pass = results.filter((r) => r.pass).length
    console.log(`\n表单化验证：通过 ${pass} / ${results.length}`)
    await browser.close()
    process.exit(pass === results.length ? 0 : 1)
  }
})()
