const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  page.on('pageerror', (e) => console.log('PAGEERR', String(e).slice(0,300)))
  page.on('console', (m) => { if (m.type() === 'error') console.log('CONSOLE', m.text().slice(0,300)) })
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
  await page.evaluate(() => {
    const tab = Array.from(document.querySelectorAll('.el-tabs__item')).find((x) => x.innerText.trim() === '角色')
    if (tab) tab.click()
  })
  await sleep(1600)
  console.log('scope values:', JSON.stringify(await page.evaluate(() => {
    const tables = Array.from(document.querySelectorAll('.el-table'))
    const t = tables.find((x) => Array.from(x.querySelectorAll('th')).some((h) => h.innerText.includes('数据范围')))
    if (!t) return null
    const heads = Array.from(t.querySelectorAll('th')).map((h) => h.innerText.trim())
    const idx = heads.indexOf('数据范围')
    return Array.from(t.querySelectorAll('.el-table__body tr')).slice(0, 6)
      .map((tr) => tr.children[idx] && tr.children[idx].innerText.trim())
  })))

  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).filter((b) => b.offsetParent)
      .find((x) => x.innerText.trim() === '配置')
    if (btn) btn.click()
  })
  await sleep(1200)
  // 功能权限 tab
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const tab = Array.from(d.querySelectorAll('.el-tabs__item')).find((x) => x.innerText.includes('功能权限'))
    if (tab) tab.click()
  })
  await sleep(1000)
  console.log('func labels:', JSON.stringify(await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const panes = Array.from(d.querySelectorAll('.el-tab-pane'))
    const pane = panes.find((p) => p.offsetParent) || panes[panes.length - 1]
    if (!pane) return { panes: 0 }
    return {
      groups: Array.from(pane.querySelectorAll('.perm-group-head .el-checkbox__label')).map((x) => x.innerText.trim()).slice(0, 5),
      res: Array.from(pane.querySelectorAll('.perm-res-head .el-checkbox__label')).map((x) => x.innerText.trim()).slice(0, 5),
      acts: Array.from(pane.querySelectorAll('.perm-actions .el-checkbox__label')).map((x) => x.innerText.trim()).slice(0, 10),
      paneText: pane.innerText.slice(0, 120).replace(/\n/g, ' | ')
    }
  })))
  await page.keyboard.press('Escape')
  await sleep(500)

  // 用户详情
  await page.evaluate(() => {
    const tab = Array.from(document.querySelectorAll('.el-tabs__item')).find((x) => x.innerText.trim() === '用户')
    if (tab) tab.click()
  })
  await sleep(1500)
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).filter((b) => b.offsetParent)
      .find((x) => x.innerText.trim() === '详情')
    if (btn) btn.click()
  })
  await sleep(1000)
  console.log('user type:', JSON.stringify(await page.evaluate(() => {
    const boxes = [...document.querySelectorAll('.el-dialog'), ...document.querySelectorAll('.el-drawer')]
    const d = boxes.find((x) => x.offsetParent)
    if (!d) return null
    const labels = Array.from(d.querySelectorAll('.el-descriptions__label'))
    const i = labels.findIndex((x) => x.innerText.includes('类型'))
    return i >= 0 ? d.querySelectorAll('.el-descriptions__content')[i].innerText.trim() : d.innerText.slice(0, 80)
  })))
  await b.close()
})()
