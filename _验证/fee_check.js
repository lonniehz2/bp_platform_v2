/**
 * 计费页验证：费用类型字典、单位下拉、规则增删改、价格配置、组织默认、域/场景中文。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1200 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 180)))
  page.on('console', (m) => { if (m.type() === 'error') console.log('控制台:', m.text().slice(0, 180)) })

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(900)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(400)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2400)

  await page.evaluate(() => { location.hash = '#/fee-items' })
  await sleep(3500)

  // 新增项目弹窗：费用类型下拉项 + 计量单位下拉
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新增项目'))
    if (b) b.click()
  })
  await sleep(1200)
  const itemForm = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    const labels = Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim())
    const selects = d.querySelectorAll('.el-select').length
    const inputs = Array.from(d.querySelectorAll('input')).map((x) => x.placeholder || '').slice(0, 8)
    return { labels, selects, inputs }
  })
  console.log('新增项目表单:', JSON.stringify(itemForm))
  await page.screenshot({ path: path.join(OUT, 'fee-item-create.png') })
  await page.keyboard.press('Escape')
  await sleep(600)

  // 规则弹窗：项目下拉 / 价格配置 / 组织
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('新增计费规则'))
    if (b) b.click()
  })
  await sleep(1200)
  const ruleForm = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    const labels = Array.from(d.querySelectorAll('.el-form-item__label')).map((x) => x.innerText.trim())
    const orgInput = Array.from(d.querySelectorAll('input')).map((x) => x.value).filter(Boolean)
    return { labels, values: orgInput.slice(0, 6) }
  })
  console.log('规则表单:', JSON.stringify(ruleForm))
  await page.screenshot({ path: path.join(OUT, 'fee-rule-create.png') })
  await page.keyboard.press('Escape')
  await sleep(600)

  // 规则列表：编辑/删除按钮
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '规则列表')
    if (b) b.click()
  })
  await sleep(2000)
  const ruleList = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    const rows = Array.from(d.querySelectorAll('.el-table__body tr')).slice(0, 2)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 140))
    return { rows, btns: Array.from(d.querySelectorAll('button')).map((b) => b.innerText.trim()).filter(Boolean).slice(0, 8) }
  })
  console.log('规则列表:', JSON.stringify(ruleList))
  await page.screenshot({ path: path.join(OUT, 'fee-rule-list.png') })
  await page.keyboard.press('Escape')
  await sleep(500)

  // 费用类型管理
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === '管理')
    if (b) b.click()
  })
  await sleep(1800)
  const ft = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    if (!d) return null
    return {
      rows: Array.from(d.querySelectorAll('.el-table__body tr')).length,
      first: (d.querySelector('.el-table__body tr')?.innerText || '').replace(/\s+/g, ' ')
    }
  })
  console.log('费用类型管理:', JSON.stringify(ft))
  await page.screenshot({ path: path.join(OUT, 'fee-types.png') })

  // 规则集域/场景中文
  await page.evaluate(() => { location.hash = '#/alerts' })
  await sleep(3800)
  const rs = await page.evaluate(() => {
    const c = Array.from(document.querySelectorAll('.page-card'))
      .find((x) => (x.querySelector('h4')?.innerText || '').includes('规则引擎'))
    if (!c) return []
    const t = c.querySelector('.el-table')
    return Array.from(t.querySelectorAll('.el-table__body tr')).slice(0, 3)
      .map((tr) => tr.innerText.replace(/\s+/g, ' ').slice(0, 110))
  })
  console.log('规则集行:', JSON.stringify(rs))
  await page.screenshot({ path: path.join(OUT, 'rules-domain.png') })

  await browser.close()
})()
