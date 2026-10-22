/** 截图角色配置弹窗（验证权限三级缩进） */
const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const b = await puppeteer.launch({
    executablePath: EDGE, headless: 'new', args: ['--no-sandbox'],
    defaultViewport: { width: 1400, height: 1000 }
  })
  const p = await b.newPage()
  const errs = []
  p.on('pageerror', (e) => errs.push(String(e).slice(0, 120)))
  await p.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
  await sleep(1200)
  await p.evaluate(() => {
    const el = document.querySelectorAll('input')
    const s = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
    }
    s(0, '350600'); s(1, 'admin'); s(2, 'admin123')
  })
  await p.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((v) => /登\s*录/.test(v.innerText || ''))
    x && x.click()
  })
  await sleep(4500)
  await p.evaluate(() => { window.location.hash = '#/rbac/role' })
  await sleep(2500)
  // 点第一行的「配置」
  const clicked = await p.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find((v) => (v.innerText || '').trim() === '配置')
    if (!btn) return false
    btn.click()
    return true
  })
  await sleep(2500)
  const info = await p.evaluate(() => {
    const dlg = document.querySelector('.el-dialog')
    if (!dlg) return { ok: false }
    return {
      ok: true,
      groups: document.querySelectorAll('.perm-group').length,
      resources: document.querySelectorAll('.perm-res').length,
      actions: document.querySelectorAll('.perm-actions .el-checkbox').length,
      text: (dlg.innerText || '').replace(/\s+/g, ' ').slice(0, 160)
    }
  })
  console.log('点击配置:', clicked, JSON.stringify(info))
  console.log('JS 报错:', errs.length ? errs.join(' | ') : '无')
  if (info.ok) await p.screenshot({ path: __dirname + '/rbac-role-config.png' })
  await b.close()
})()
