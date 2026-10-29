const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1500, height: 950 })
  await page.setCacheEnabled(false)
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(300)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('登'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)
  await page.evaluate(() => { location.hash = '#/rbac' })
  await sleep(3000)

  console.log('tabs:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-tabs__item')).map((x) => x.innerText.trim()))))
  // 角色列表数据范围列
  console.log('role rows:', JSON.stringify(await page.evaluate(() => {
    const t = document.querySelector('.el-table')
    if (!t) return null
    const heads = Array.from(t.querySelectorAll('.el-table__header th')).map((h) => h.innerText.trim())
    const idx = heads.indexOf('数据范围')
    const tr = t.querySelector('.el-table__body tr')
    return tr ? { heads, scope: tr.children[idx] && tr.children[idx].innerText.trim() } : null
  })))

  // 打开角色配置
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '配置')
    if (btn) btn.click()
  })
  await sleep(1200)
  console.log('page perms:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return Array.from(d.querySelectorAll('.perm-actions .el-checkbox__label'))
      .map((x) => x.innerText.trim()).slice(0, 8)
  })))
  // 切到功能权限
  await page.evaluate(() => {
    const tab = Array.from(document.querySelectorAll('.el-dialog .el-tabs__item'))
      .find((x) => x.innerText.includes('功能权限'))
    if (tab) tab.click()
  })
  await sleep(900)
  console.log('func perms:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return Array.from(d.querySelectorAll('.perm-actions .el-checkbox__label'))
      .map((x) => x.innerText.trim()).slice(0, 10)
  })))
  await b.close()
})()
