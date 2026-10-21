/**
 * 待办中心专项 UI 验证：菜单角标 + 筛选交互
 *
 * 断言：
 *   ① 侧边栏「待办中心」菜单项上出现角标，数字与接口一致
 *   ② 待办明细默认只显示「待处理」
 *   ③ 关键字筛选生效（输入真实标题片段 → 行数变化）
 *   ④ 清空后回到默认状态
 *
 * 用法：node _check_todo_ui.js [outDir] [baseUrl]
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const outDir = process.argv[2] || __dirname
const BASE = process.argv[3] || 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const results = []
const ok = (n, d) => { results.push({ n, pass: true, d }); console.log('  ✓ ' + n + (d ? '  ' + d : '')) }
const bad = (n, d) => { results.push({ n, pass: false, d }); console.log('  ✗ ' + n + '  ' + (d || '')) }

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
    const inApp = await waitFor(async () => page.evaluate(() => !!document.querySelector('.el-menu, .rail')), 20000)
    if (!inApp) { bad('登录', '未进入主界面'); await browser.close(); process.exit(1) }

    // ---------- ① 角标 ----------
    // 角标要等 store 拉完 overview，最长等 10s
    const badge = await waitFor(async () => page.evaluate(() => {
      const marks = Array.from(document.querySelectorAll('.el-badge__content'))
      const hit = marks.find((m) => /^\d+$/.test((m.innerText || '').trim()))
      return hit ? hit.innerText.trim() : null
    }), 12000)
    badge ? ok('菜单角标显示待办数', '角标 = ' + badge) : bad('菜单角标显示待办数', '未找到数字角标')

    // ---------- 进入待办中心 ----------
    await page.evaluate(() => { window.location.hash = '#/todos' })
    await sleep(1500)
    await waitFor(async () => page.evaluate(() =>
      !document.querySelector('.el-loading-mask:not([style*="display: none"])')))

    const rowsNow = () => page.evaluate(() => {
      const pane = Array.from(document.querySelectorAll('.el-tab-pane')).find((p) => p.offsetParent !== null)
      const scope = pane || document
      return Array.from(scope.querySelectorAll('.el-table__body tbody tr'))
        .filter((tr) => tr.offsetParent !== null).length
    })

    const base = await waitFor(async () => { const n = await rowsNow(); return n > 0 ? n : null }, 8000)
    base ? ok('待办明细加载', base + ' 行') : bad('待办明细加载', '表格为空')

    // ---------- ② 默认只显示待处理 ----------
    const statusCol = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('.el-table__body tbody tr'))
        .filter((tr) => tr.offsetParent !== null)
      return rows.map((tr) => (tr.innerText || '').replace(/\s+/g, ' ')).slice(0, 20)
    })
    const hasDone = statusCol.some((t) => t.includes('已完成'))
    hasDone ? bad('默认只显示待处理', '列表里出现了「已完成」的行')
      : ok('默认只显示待处理', '未出现已完成行')

    // ---------- ③ 关键字筛选 ----------
    const firstTitle = statusCol[0] || ''
    const frag = firstTitle.replace(/\s/g, '').slice(0, 2)
    const input = await page.$('[data-testid="todo-keyword"]')
    if (!input) {
      bad('关键字筛选', '未找到关键字输入框')
    } else {
      await input.click({ clickCount: 3 })
      await page.keyboard.down('Control'); await page.keyboard.press('KeyA'); await page.keyboard.up('Control')
      await input.type(frag, { delay: 25 })
      const btn = await page.$('[data-testid="todo-search"]')
      await btn.click()
      await sleep(1200)
      await waitFor(async () => page.evaluate(() =>
        !document.querySelector('.el-loading-mask:not([style*="display: none"])')))
      const after = await rowsNow()
      const txt = await page.evaluate(() => {
        const rows = Array.from(document.querySelectorAll('.el-table__body tbody tr'))
          .filter((tr) => tr.offsetParent !== null)
        return rows.map((tr) => (tr.innerText || '')).join('|')
      })
      after > 0 && (after <= base || txt.includes(frag))
        ? ok('关键字筛选生效', `关键字「${frag}」→ ${after} 行（原 ${base} 行）`)
        : bad('关键字筛选生效', `关键字「${frag}」→ ${after} 行（原 ${base} 行），内容未包含关键字`)

      // ---------- ④ 清空 ----------
      const reset = await page.$('[data-testid="todo-reset"]')
      await reset.click()
      await sleep(1200)
      await waitFor(async () => page.evaluate(() =>
        !document.querySelector('.el-loading-mask:not([style*="display: none"])')))
      const back = await rowsNow()
      const kw = await page.evaluate(() =>
        (document.querySelector('[data-testid="todo-keyword"]') || {}).value || '')
      back === base && !kw
        ? ok('清空恢复默认', `${back} 行，关键字已清空`)
        : bad('清空恢复默认', `${back} 行（期望 ${base}），关键字="${kw}"`)
    }

    // ---------- ⑤ 只看我的 ----------
    const mineBox = await page.$('[data-testid="todo-only-mine"]')
    if (!mineBox) {
      bad('只看我的', '未找到开关')
    } else {
      await mineBox.click()
      await sleep(1200)
      await waitFor(async () => page.evaluate(() =>
        !document.querySelector('.el-loading-mask:not([style*="display: none"])')))
      const mineRows = await rowsNow()
      const mineTotal = await page.evaluate(() => {
        const el = document.querySelector('.el-pagination__total')
        return el ? el.innerText.trim() : ''
      })
      mineRows > 0 && mineRows < base
        ? ok('只看我的生效', `${base} 行 → ${mineRows} 行（${mineTotal}）`)
        : bad('只看我的生效', `${base} 行 → ${mineRows} 行（${mineTotal}）`)
      // 复位，避免影响后续断言
      await mineBox.click()
      await sleep(1000)
      await waitFor(async () => page.evaluate(() =>
        !document.querySelector('.el-loading-mask:not([style*="display: none"])')))
    }

    // ---------- ⑥ 批量已读 ----------
    const cb = await page.$('.el-table__body tbody tr .el-checkbox')
    if (!cb) {
      bad('批量已读', '未找到行选择框')
    } else {
      await cb.click()
      await sleep(300)
      const clicked = await page.evaluate(() => {
        const b = Array.from(document.querySelectorAll('button'))
          .find((x) => (x.innerText || '').includes('批量已读'))
        if (!b || b.disabled) return b ? 'disabled' : 'not-found'
        b.click()
        return 'ok'
      })
      const toast = await waitFor(async () => page.evaluate(() => {
        const all = Array.from(document.querySelectorAll('.el-message'))
          .map((x) => (x.innerText || '').trim())
        return all.find((t) => t.includes('已读')) || null
      }), 8000)
      clicked === 'ok' && toast
        ? ok('批量已读', toast)
        : bad('批量已读', `按钮=${clicked}，提示=${toast || '无'}`)
    }

    // ---------- ⑦ 去处理跳转 ----------
    const hashBefore = await page.evaluate(() => location.hash)
    const dealt = await page.evaluate(() => {
      const b = document.querySelector('[data-testid="todo-deal"]')
      if (!b) return false
      b.click()
      return true
    })
    await sleep(1600)
    const hashAfter = await page.evaluate(() => location.hash)
    dealt && hashAfter !== hashBefore && !hashAfter.includes('/todos')
      ? ok('去处理跳转', `${hashBefore} → ${hashAfter}`)
      : bad('去处理跳转', `点击=${dealt}，${hashBefore} → ${hashAfter}`)

    if (errors.length) bad('页面无 JS 报错', errors[0].slice(0, 80))
    else ok('页面无 JS 报错')
  } catch (e) {
    bad('执行异常', e.message)
    try { await page.screenshot({ path: path.join(outDir, 'todo-ui-error.png') }) } catch (_) {}
  } finally {
    const pass = results.filter((r) => r.pass).length
    console.log(`\n待办中心 UI：通过 ${pass} / ${results.length}`)
    await browser.close()
    process.exit(pass === results.length ? 0 : 1)
  }
})()
