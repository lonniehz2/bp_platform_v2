/**
 * 本轮 9 项 UI 修复验证（可自动核对的部分）+ 截图。
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
  await page.setViewport({ width: 1560, height: 1040 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 170)))

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
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

  // 房源台账：新增弹窗的空间树 + 朝向
  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(2600)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('新增房源'))
    if (b) b.click()
  })
  await sleep(2000)
  const houseForm = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    if (!dlg) return { ok: false }
    const labels = Array.from(dlg.querySelectorAll('.el-form-item__label'))
      .map((x) => x.innerText.trim())
    const selects = dlg.querySelectorAll('.el-select, .el-tree-select').length
    return { ok: true, labels: labels.slice(0, 14), selects }
  })
  console.log('新增房源表单:', JSON.stringify(houseForm).slice(0, 260))
  await page.screenshot({ path: path.join(OUT, 'fix-house-create.png') })

  // 关闭弹窗
  await page.keyboard.press('Escape')
  await sleep(600)

  // 床位管理：房间下拉是否有数据
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('床位管理'))
    if (b) b.click()
  })
  await sleep(2200)
  const bed = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    const sel = dlg?.querySelector('.el-select, .el-tree-select input')
    return { dialog: !!dlg, placeholder: sel?.getAttribute('placeholder') }
  })
  // 点开下拉看候选数量
  const bedOptions = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    const inp = dlg?.querySelector('.el-select .el-input__inner, .el-tree-select .el-input__inner')
    if (inp) inp.click()
    return true
  })
  await sleep(1500)
  const bedCount = await page.evaluate(() =>
    document.querySelectorAll('.el-select-dropdown__item, .el-tree-node').length)
  console.log('床位房间下拉:', JSON.stringify(bed), '候选节点:', bedCount)
  await page.screenshot({ path: path.join(OUT, 'fix-bed-room.png') })
  await page.keyboard.press('Escape')
  await sleep(600)

  // 空间层级：详情面板编辑/删除
  await page.evaluate(() => { location.hash = '#/spaces' })
  await sleep(2600)
  await page.evaluate(() => {
    const node = document.querySelector('.el-tree-node__content')
    if (node) node.click()
  })
  await sleep(1200)
  const spaceBtns = await page.evaluate(() => {
    const row = document.querySelector('.toolbar')
    return Array.from(document.querySelectorAll('.page-card button'))
      .map((b) => b.innerText.trim()).filter((t) => ['编辑', '删除', '在此节点下新增'].includes(t))
  })
  console.log('空间层级按钮:', spaceBtns.join(' / ') || '未找到')
  await page.screenshot({ path: path.join(OUT, 'fix-space-edit.png') })

  // 日房态：房源下拉
  await page.evaluate(() => { location.hash = '#/house-calendar' })
  await sleep(2800)
  const cal = await page.evaluate(() => {
    const inp = Array.from(document.querySelectorAll('input'))
      .find((x) => (x.getAttribute('placeholder') || '').includes('房源名称'))
    return { hasSelect: !!inp, placeholder: inp?.getAttribute('placeholder') }
  })
  console.log('日房态筛选:', JSON.stringify(cal))
  await page.screenshot({ path: path.join(OUT, 'fix-calendar.png') })

  // 房源详情：朝向/租金单位/计量模式 中文
  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(2500)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-table__body button'))
      .find((x) => x.innerText.includes('详情'))
    if (b) b.click()
  })
  await sleep(1800)
  const detail = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    const txt = dlg ? dlg.innerText.replace(/\s+/g, ' ') : ''
    const hit = ['朝向', '计价单位', '计量模式'].map((k) => {
      const i = txt.indexOf(k)
      return i < 0 ? k + ':未找到' : txt.slice(i, i + 26)
    })
    return hit
  })
  console.log('详情字段:', detail.join(' | ').slice(0, 220))
  await page.screenshot({ path: path.join(OUT, 'fix-house-detail.png') })

  await browser.close()
})()
