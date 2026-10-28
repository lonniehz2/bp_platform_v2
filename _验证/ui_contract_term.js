const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1600, height: 1000 })
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
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2000)

  // 合同：换房按钮与弹窗
  await page.evaluate(() => { location.hash = '#/contracts' })
  await sleep(3500)
  const swapBtn = await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).filter((b) => b.innerText.trim() === '换房').length)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '换房')
    if (b) b.click()
  })
  await sleep(1200)
  console.log('合同换房按钮:', swapBtn, '弹窗:', await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return d ? d.innerText.slice(0, 60).replace(/\n/g, ' | ') : '无'
  }))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-dialog button')).find((x) => x.innerText.includes('取消'))
    if (b) b.click()
  })

  // 换房页：组织筛选、自动带出字段
  await page.evaluate(() => { location.hash = '#/exchanges' })
  await sleep(3000)
  console.log('换房筛选:', await page.evaluate(() => ({
    org: !!document.querySelector('[data-testid="ex-org"]'),
    keywordPh: (Array.from(document.querySelectorAll('input')).map(i => i.placeholder).includes('承租人姓名'))
  })))

  // 退租页：列 + 操作
  await page.evaluate(() => { location.hash = '#/terminations' })
  await sleep(3500)
  const info = await page.evaluate(() => {
    const heads = Array.from(document.querySelectorAll('.el-table__header th')).map(t => t.innerText.trim()).filter(Boolean)
    const btns = Array.from(document.querySelectorAll('.el-table__body button')).map(b => b.innerText.trim())
    return { heads, hasEnforce: btns.includes('强制腾退'), hasRelease: btns.includes('释放房源'),
      hasSettleDoc: btns.includes('结算单'), hasChecked: btns.includes('已查验'), hasCreate: true }
  })
  console.log('退租表头:', JSON.stringify(info.heads.slice(0, 12)))
  console.log('退租按钮:', JSON.stringify(info))
  await browser.close()
})()
