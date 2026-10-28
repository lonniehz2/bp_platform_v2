const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1000 })
  await page.setCacheEnabled(false)
  const bad = []
  page.on('response', async (res) => {
    const u = res.url()
    if (u.includes('/api/') && res.status() >= 400) {
      let body = ''
      try { body = (await res.text()).slice(0, 120) } catch (e) {}
      bad.push(res.status() + ' ' + u.replace(BASE, '') + ' ' + body)
    }
  })
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2000)

  // 1) 公示管理：无 404 / 无报错提示
  await page.evaluate(() => { location.hash = '#/publicities' })
  await sleep(3500)
  const pubBad = bad.filter((x) => x.includes('/winners'))
  console.log('公示页 winners 错误:', pubBad.length ? pubBad : '无 ✔')

  // 2) 申请受理：补件按钮 / 组织选择
  await page.evaluate(() => { location.hash = '#/applications' })
  await sleep(3500)
  const app = await page.evaluate(() => {
    const rows = Array.from(document.querySelectorAll('.el-table__body tr'))
    return {
      supplementBtn: Array.from(document.querySelectorAll('button'))
        .filter((b) => b.innerText.trim() === '补件完成').length
    }
  })
  console.log('补件按钮数量:', app.supplementBtn)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新建申请'))
    if (b) b.click()
  })
  await sleep(1200)
  const orgField = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return 'no-dialog'
    const labels = Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim())
    const isSelect = !!d.querySelector('.el-select, .el-select-v2, .org-select')
    return JSON.stringify({ labels: labels.filter((x) => x.includes('组织')), isSelect })
  })
  console.log('新建申请组织字段:', orgField)
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const b = d && Array.from(d.querySelectorAll('button')).find((x) => x.innerText.includes('取消'))
    if (b) b.click()
  })

  // 3) 轮候管理：中签状态
  await page.evaluate(() => { location.hash = '#/waitlist' })
  await sleep(3000)
  const won = await page.evaluate(() => { const t=document.body.innerText; return { hasZhongqian: t.includes('中签'), sample: (t.match(/中签/g)||[]).length } })
  console.log('轮候页显示已中签:', won)
  await browser.close()
})()
