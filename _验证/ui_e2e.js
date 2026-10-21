/**
 * UI E2E 交互测试：真实点按钮、填表单、断言结果
 *
 * 设计要点：
 *   1. 断言全部「轮询等待」，不用固定 sleep
 *   2. SPA 内跳转用 location.hash，不重载文档（消息观察器存活）
 *   3. 行查找限定在「当前可见 tab 面板」内
 *   4. 表单字段用 data-testid 语义定位
 *   5. 消息按「动作前打标记、只取之后新增的」——避免读到登录那条旧提示
 *   6. 关键结果同时用接口二次校验，失败即自带诊断信息
 *
 * 覆盖闭环：
 *   ① 保障对象：新增 → 接口确认 → 搜索到 → 改状态黑名单 → 接口确认
 *   ② 计费项目：新增 → 停用/启用
 *   ③ 合同：新建（9 项必填）→ 搜索到 → 提交待签 → 开始签约 → 签约生效
 *
 * 用法：node ui_e2e.js <outDir> [baseUrl]
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const outDir = process.argv[2] || __dirname
const BASE = process.argv[3] || 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const stamp = String(Date.now()).slice(-6)

const results = []
function ok(name, detail) { results.push({ name, pass: true, detail }); console.log('  ✓ ' + name + (detail ? '  ' + detail : '')) }
function bad(name, detail) { results.push({ name, pass: false, detail }); console.log('  ✗ ' + name + '  ' + (detail || '')) }

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
    defaultViewport: { width: 1600, height: 950 }
  })
  const page = await browser.newPage()
  const pageErrors = []
  page.on('pageerror', (e) => { pageErrors.push(e.message); console.log('  [pageerror] ' + e.message.slice(0, 120)) })

  const waitFor = async (fn, timeout = 8000, interval = 150) => {
    const t0 = Date.now()
    let last = null
    while (Date.now() - t0 < timeout) {
      last = await fn()
      if (last) return last
      await sleep(interval)
    }
    return last
  }

  // ---------- 登录 ----------
  await page.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
  await waitFor(async () => page.evaluate(() => document.querySelectorAll('input').length >= 3), 15000)
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
  const loggedIn = await waitFor(async () => page.evaluate(() => !!document.querySelector('.el-menu, .rail')), 20000)
  if (!loggedIn) {
    bad('登录', '20 秒内未进入主界面')
    await page.screenshot({ path: path.join(outDir, 'e2e-login-fail.png') })
    await browser.close()
    process.exit(1)
  }

  // 累积页面提示（ElMessage）：按 DOM 节点去重，避免同一 toast 被反复扫描
  await page.evaluate(() => {
    window.__msgs = []
    const scan = () => {
      document.querySelectorAll('.el-message').forEach((m) => {
        if (m.__seen) return
        const t = (m.innerText || '').trim()
        if (!t) return
        m.__seen = true
        const kind = (m.className || '').includes('success') ? 'OK'
          : (m.className || '').includes('warning') ? 'WARN' : 'ERR'
        window.__msgs.push(kind + ':' + t)
      })
    }
    new MutationObserver(scan).observe(document.body, { childList: true, subtree: true })
    scan()
  })
  const msgs = () => page.evaluate(() => (window.__msgs || []).slice())
  let msgMark = 0
  /** 动作前打标记：之后只看新增提示 */
  const mark = async () => { msgMark = (await msgs()).length }
  const newMsgs = async () => {
    const all = await msgs()
    const fresh = []
    for (const m of all.slice(msgMark)) if (fresh[fresh.length - 1] !== m) fresh.push(m)
    return fresh
  }
  const waitMsg = async (prefix, timeout = 10000) =>
    waitFor(async () => (await newMsgs()).find((m) => m.startsWith(prefix + ':')) || null, timeout)
  const diag = async () => {
    const a = await newMsgs()
    return a.length ? '页面提示：' + a.join(' | ') : '无新提示'
  }

  const token = await page.evaluate(() => localStorage.getItem('bp_token') || localStorage.getItem('token'))
  const api = async (p, method = 'GET', body) => page.evaluate(async (url, m, b, t) => {
    const res = await fetch(url, {
      method: m,
      headers: { 'Content-Type': 'application/json', 'X-Tenant-Id': '350600', Authorization: 'Bearer ' + t },
      body: b ? JSON.stringify(b) : undefined
    })
    try { return await res.json() } catch (_) { return { httpStatus: res.status } }
  }, BASE + p, method, body, token || '')

  const goHash = async (hash, settle = 800) => {
    await page.evaluate((h) => { window.location.hash = h }, hash)
    await sleep(settle)
    await waitFor(async () => page.evaluate(() =>
      !document.querySelector('.el-loading-mask:not([style*="display: none"])')), 8000)
    await sleep(200)
  }

  const clickByText = async (text) => page.evaluate((t) => {
    const norm = (s) => (s || '').replace(/\s/g, '')
    const el = Array.from(document.querySelectorAll('button, .el-button, a'))
      .filter((x) => x.offsetParent !== null)
      .find((x) => norm(x.innerText) === norm(t))
    if (el) { el.click(); return true }
    return false
  }, text)

  /** 可见的最上层弹窗（页面上多个 el-dialog 同时存在于 DOM，隐藏的也在） */
  const visibleDialog = () => page.evaluateHandle(() => {
    const ds = Array.from(document.querySelectorAll('.el-dialog')).filter((d) => d.offsetParent !== null)
    return ds[ds.length - 1] || null
  })

  /**
   * 点弹窗底部按钮：等按钮出现再点（最多 5s）。
   * 早期版本是「固定 sleep 后点击」，弹窗动画慢一点就点空，表现为「点了没反应」。
   */
  const clickDlg = async (text) => {
    const done = await waitFor(async () => {
      const dlg = await visibleDialog()
      const el = dlg.asElement()
      if (!el) return false
      return el.evaluate((d, t) => {
        const norm = (s) => (s || '').replace(/\s/g, '')
        const b = Array.from(d.querySelectorAll('button')).find((x) => norm(x.innerText) === norm(t))
        if (!b) return false
        b.click()
        return true
      }, text)
    }, 5000, 200)
    return !!done
  }

  const rowTexts = () => page.evaluate(() => {
    const pane = Array.from(document.querySelectorAll('.el-tab-pane')).find((p) => p.offsetParent !== null)
    const scope = pane || document
    return Array.from(scope.querySelectorAll('.el-table__body tbody tr'))
      .filter((tr) => tr.offsetParent !== null)
      .map((tr) => (tr.innerText || '').replace(/\s+/g, ' ').trim())
  })

  const clickRowButton = (matchText, btnText) => page.evaluate((m, b) => {
    const pane = Array.from(document.querySelectorAll('.el-tab-pane')).find((p) => p.offsetParent !== null)
    const scope = pane || document
    const rows = Array.from(scope.querySelectorAll('.el-table__body tbody tr'))
      .filter((tr) => tr.offsetParent !== null)
    const row = rows.find((tr) => (tr.innerText || '').includes(m))
    if (!row) return 'no-row'
    const norm = (s) => (s || '').replace(/\s/g, '')
    const btns = Array.from(row.querySelectorAll('button'))
    const btn = btns.find((x) => norm(x.innerText) === norm(b)) || btns.find((x) => (x.innerText || '').includes(b))
    if (!btn) return 'no-btn:' + btns.map((x) => norm(x.innerText)).join('/')
    btn.click()
    return 'ok'
  }, matchText, btnText)

  const fillTid = async (tid, val) => {
    const dlg = await visibleDialog()
    const el = dlg.asElement()
    const apply = (root, id, v) => {
      const host = root.querySelector('[data-testid="' + id + '"]')
      if (!host) return false
      const input = host.tagName === 'INPUT' || host.tagName === 'TEXTAREA'
        ? host : host.querySelector('input, textarea')
      if (!input) return false
      const proto = input.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype
      Object.getOwnPropertyDescriptor(proto, 'value').set.call(input, v)
      input.dispatchEvent(new Event('input', { bubbles: true }))
      input.dispatchEvent(new Event('change', { bubbles: true }))
      input.dispatchEvent(new Event('blur', { bubbles: true }))
      return true
    }
    if (el && await el.evaluate(apply, tid, val)) return true
    return page.evaluate(() => false)
  }

  /** 点击兜底：元素被重渲染导致鼠标点击失败时，退化为 JS click */
  const safeClick = async (h, opts) => {
    if (!h) return false
    try { await h.click(opts); return true } catch (_) {}
    try { await h.evaluate((el) => el.click()); return true } catch (_) { return false }
  }

  /** 日期：真实键盘输入 + Enter 提交 */
  const fillDate = async (tid, val) => {
    const dlg = await visibleDialog()
    const el = dlg.asElement()
    if (!el) return null
    const input = await el.$('[data-testid="' + tid + '"] input')
    if (!input) return null
    await safeClick(input)
    await sleep(200)
    await page.keyboard.down('Control'); await page.keyboard.press('KeyA'); await page.keyboard.up('Control')
    await input.type(val, { delay: 20 })
    await page.keyboard.press('Enter')
    await sleep(350)
    return input.evaluate((i) => i.value || '')
  }

  /** 工具栏按 placeholder 用真实键盘输入（保证 v-model 更新） */
  const typeSearch = async (placeholder, val) => {
    const handles = await page.$$('input')
    for (const h of handles) {
      const info = await h.evaluate((el) => ({ vis: el.offsetParent !== null, ph: el.placeholder || '' }))
      if (info.vis && info.ph.includes(placeholder)) {
        await safeClick(h, { clickCount: 3 })
        await page.keyboard.down('Control'); await page.keyboard.press('KeyA'); await page.keyboard.up('Control')
        await h.type(val, { delay: 20 })
        const got = await h.evaluate((el) => el.value)
        return { ok: true, got }
      }
    }
    return { ok: false, got: '' }
  }

  /** 弹窗下拉：真实鼠标点击后选可见项 */
  const pickSelect = async (optionText) => {
    const dlg = await visibleDialog()
    const el = dlg.asElement()
    if (!el) return 'no-dialog'
    const w = (await el.$('.el-select__wrapper')) || (await el.$('.el-select'))
    if (!w) return 'no-select'
    if (!(await safeClick(w))) return 'click-fail'
    await sleep(500)
    const items = await page.$$('.el-select-dropdown__item')
    for (const it of items) {
      const vis = await it.evaluate((n) => n.offsetParent !== null).catch(() => false)
      if (!vis) continue
      const txt = await it.evaluate((n) => (n.innerText || '').trim()).catch(() => '')
      if (txt.includes(optionText)) {
        if (await safeClick(it)) return 'ok'
        return 'option-click-fail'
      }
    }
    const visible = []
    for (const it of items) {
      const vis = await it.evaluate((n) => n.offsetParent !== null).catch(() => false)
      if (vis) visible.push(await it.evaluate((n) => (n.innerText || '').trim()).catch(() => ''))
    }
    return 'no-option:' + visible.join('/')
  }

  try {
    // ================= ① 保障对象：新增 → 搜索 → 改状态 =================
    console.log('\n① 保障对象：新增人员 → 搜索 → 改状态')
    await goHash('#/persons', 1200)
    const name = 'E2E人员' + stamp
    const phone = '139' + stamp.padStart(8, '0')
    if (!(await clickByText('新增人员'))) {
      bad('打开新增人员弹窗', '未找到「新增人员」按钮')
    } else {
      const hasDlg = await waitFor(async () => page.evaluate(() =>
        !!document.querySelector('.el-dialog [data-testid="person-name"]')), 5000)
      if (!hasDlg) bad('打开新增人员弹窗', '弹窗内无 person-name 控件')
      await fillTid('person-name', name)
      await fillTid('person-phone', phone)
      await mark()
      await clickDlg('保存')
      const m = await waitMsg('OK', 10000)
      if (m) ok('新增人员提交', m.replace('OK:', ''))
      else bad('新增人员提交', await diag())

      // 接口侧确认真的落库了
      const chk = await api('/api/v1/persons?pageNum=1&pageSize=5&keyword=' + encodeURIComponent(name))
      const found = ((chk.data || {}).rows || []).find((r) => r.personName === name)
      if (found) ok('接口确认人员已入库', 'id=' + found.id)
      else bad('接口确认人员已入库', '按姓名查不到 ' + name)

      // 界面侧：搜索定位（列表按 id 倒序，种子 id 更大，新记录不会出现在首页）
      await goHash('#/persons', 900)
      const typed = await typeSearch('姓名', name)
      await clickByText('查询')
      const hit = await waitFor(async () => (await rowTexts()).find((t) => t.includes(name)), 8000)
      if (hit) {
        ok('搜索到新增人员', hit.slice(0, 46))
      } else {
        const rows = await rowTexts()
        bad('搜索到新增人员', `输入框取值=${JSON.stringify(typed.got)}，共 ${rows.length} 行，首行=${(rows[0] || '').slice(0, 40)}`)
      }

      // 改状态 → 黑名单
      const clickRes = await clickRowButton(name, '改状态')
      if (clickRes !== 'ok') {
        bad('点击改状态', clickRes === 'no-row' ? '未找到该人员行' : '行内无改状态按钮：' + clickRes)
      } else {
        await sleep(400)
        const picked = await pickSelect('黑名单')
        await sleep(200)
        await mark()
        await clickDlg('确认')
        const m2 = await waitMsg('OK', 10000)
        const after = await waitFor(async () => {
          const t = (await rowTexts()).find((x) => x.includes(name))
          return t && t.includes('黑名单') ? t : null
        }, 8000)
        const chk2 = found ? await api('/api/v1/persons/' + found.id) : null
        const apiStatus = ((chk2 || {}).data || {}).personStatus
        picked === 'ok' && after && apiStatus === 'BLACKLIST'
          ? ok('改状态为黑名单', '列表与接口均已反映（' + apiStatus + '）')
          : bad('改状态为黑名单', `选下拉=${picked}；列表=${after ? '已反映' : '未反映'}；接口=${apiStatus}；${m2 || (await diag())}`)
      }
    }

    // ================= ② 计费项目：新增 → 停用/启用 =================
    console.log('\n② 计费项目：新增 → 停用/启用')
    await goHash('#/fee-items', 1200)
    const feeCode = 'E2E' + stamp
    if (!(await clickByText('新增项目'))) {
      bad('打开新增项目弹窗', '未找到「新增项目」按钮')
    } else {
      const hasDlg = await waitFor(async () => page.evaluate(() =>
        !!document.querySelector('.el-dialog [data-testid="fee-code"]')), 5000)
      if (!hasDlg) bad('打开新增项目弹窗', '弹窗内无 fee-code 控件')
      await fillTid('fee-code', feeCode)
      await fillTid('fee-name', 'E2E测试项目' + stamp)
      await fillTid('fee-price', '12.5')
      await mark()
      await clickDlg('保存')
      const m = await waitMsg('OK', 10000)
      await goHash('#/fee-items', 900)
      const row = await waitFor(async () => (await rowTexts()).find((t) => t.includes(feeCode)), 8000)
      if (!row) {
        bad('新增计费项目', `未出现新行 ${feeCode}；${m || (await diag())}`)
      } else {
        ok('新增计费项目', m ? m.replace('OK:', '') : row.slice(0, 40))
        const before = row
        const target = before.includes('停用') ? '停用' : '启用'
        await mark()
        const res = await clickRowButton(feeCode, target)
        const m2 = await waitMsg('OK', 10000)
        const toggled = res === 'ok' && await waitFor(async () => {
          const t = (await rowTexts()).find((x) => x.includes(feeCode))
          return t && t !== before ? t : null
        }, 8000)
        toggled
          ? ok('切换计费项目状态', `点击「${target}」→ ` + ((m2 || '').replace('OK:', '') || '行状态已变化'))
          : bad('切换计费项目状态', res === 'ok' ? '行状态未变化；' + (await diag()) : '按钮点击失败：' + res)
      }
    }

    // ================= ③ 合同：新建 → 提交待签 → 开始签约 → 签约 =================
    console.log('\n③ 合同：新建 → 提交待签 → 开始签约 → 签约生效')
    const houses = await api('/api/v1/houses?pageNum=1&pageSize=5&houseStatus=VACANT')
    const persons = await api('/api/v1/persons?pageNum=1&pageSize=3')
    const h = ((houses.data || {}).rows || [])[0]
    const p = ((persons.data || {}).rows || [])[0]
    if (!h || !p || !h.spaceId) {
      bad('准备合同数据', `缺少空置房源（或 spaceId）或人员：house=${!!h} space=${!!(h && h.spaceId)} person=${!!p}`)
    } else {
      await goHash('#/contracts', 1200)
      if (!(await clickByText('新建合同'))) {
        bad('打开新建合同弹窗', '未找到按钮')
      } else {
        const hasDlg = await waitFor(async () => page.evaluate(() =>
          !!document.querySelector('.el-dialog [data-testid="c-lessee-id"]')), 5000)
        if (!hasDlg) bad('打开新建合同弹窗', '弹窗内无 c-lessee-id 控件')
        await fillTid('c-org-id', String(h.orgId || 1))
        await fillTid('c-lessor-org-id', String(h.ownerOrgId || h.orgId || 1))
        await fillTid('c-lessee-id', String(p.id))
        await fillTid('c-lessee-name', p.personName || 'E2E承租人')
        await fillTid('c-lessee-phone', '13900002222')
        await fillTid('c-house-id', String(h.id))
        await fillTid('c-space-id', String(h.spaceId))
        await fillTid('c-address', h.houseName || 'E2E地址')
        await fillTid('c-rent-price', String(h.rentStandard || 20))
        await fillTid('c-rent', '1000')
        await fillTid('c-deposit', '1000')
        const d1 = await fillDate('c-lease-start', '2026-11-01')
        const d2 = await fillDate('c-lease-end', '2027-10-31')

        await mark()
        await clickDlg('保存')
        const m = await waitMsg('OK', 12000)
        const cl = await api('/api/v1/contracts?pageNum=1&pageSize=1')
        const cNew = ((cl.data || {}).rows || [])[0]
        if (m && cNew) {
          ok('新建合同', `${m.replace('OK:', '')}，合同号 ${cNew.contractNo}，租期 ${d1}~${d2}`)

          await goHash('#/contracts', 900)
          const typed = await typeSearch('合同号', cNew.contractNo)
          await clickByText('查询')
          const row = await waitFor(async () => (await rowTexts()).find((t) => t.includes(cNew.contractNo)), 8000)
          if (!row) {
            bad('搜索到新合同', `输入=${JSON.stringify(typed.got)}，未找到 ${cNew.contractNo}`)
          } else {
            ok('搜索到新合同', row.slice(0, 46))
            const chain = [
              ['提交待签', '已提交待签', 'PENDING_SIGN'],
              ['开始签约', '已进入签约中', 'SIGNING'],
            ]
            let state = cNew.contractStatus
            let failed = null
            for (const [btn, expectMsg, expectStatus] of chain) {
              await mark()
              const r = await clickRowButton(cNew.contractNo, btn)
              if (r !== 'ok') { failed = `「${btn}」按钮不可用：${r}`; break }
              const mm = await waitMsg('OK', 10000)
              const cur = await api('/api/v1/contracts/' + cNew.id)
              state = ((cur.data || {}).contractStatus) || state
              if (!mm || state !== expectStatus) {
                failed = `「${btn}」→ 提示 ${mm ? mm.replace('OK:', '') : '无'}，状态 ${state}（期望 ${expectStatus}）`
                break
              }
            }
            // 最后一步：签约弹窗
            if (!failed) {
              await mark()
              const r = await clickRowButton(cNew.contractNo, '签约')
              if (r !== 'ok') {
                failed = '「签约」按钮不可用：' + r
              } else {
                await sleep(500)
                await clickDlg('确认签约')
                const mm = await waitMsg('OK', 12000)
                const cur = await api('/api/v1/contracts/' + cNew.id)
                state = ((cur.data || {}).contractStatus) || state
                if (!mm || state !== 'EFFECTIVE') {
                  failed = `签约 → 提示 ${mm ? mm.replace('OK:', '') : '无'}，状态 ${state}`
                }
              }
            }
            if (failed) {
              // 失败时把本轮所有提示（含 ERR/WARN）一起打出来，否则看不到后端拒绝原因
              bad('合同签约生效', failed + ' ｜ ' + (await diag()))
            } else {
              ok('合同签约生效', '草稿 → 待签约 → 签约中 → 履约中（合同号 ' + cNew.contractNo + '）')
              // 合同驱动房源占用：生效后房源必须变为已入住
              const hd = await api('/api/v1/houses/' + cNew.houseId)
              const hs = ((hd || {}).data || {}).houseStatus
              hs === 'OCCUPIED'
                ? ok('签约后房源被占用', '房源状态 → ' + hs)
                : bad('签约后房源被占用', '房源状态仍为 ' + hs + '（合同已履约但房源未占房，可被重复配租）')
            }
          }
        } else {
          bad('新建合同', `${m || (await diag())}，租期回填 ${d1}~${d2}`)
        }
      }
    }
  } catch (e) {
    bad('执行异常', e.message)
    try { await page.screenshot({ path: path.join(outDir, 'e2e-error.png') }) } catch (_) {}
  } finally {
    const pass = results.filter((r) => r.pass).length
    fs.writeFileSync(path.join(outDir, 'ui-e2e.json'),
      JSON.stringify({ base: BASE, pass, total: results.length, results, pageErrors }, null, 1), 'utf8')
    console.log(`\nE2E 结果：通过 ${pass} / ${results.length}`)
    await browser.close()
    process.exit(pass === results.length ? 0 : 1)
  }
})()
