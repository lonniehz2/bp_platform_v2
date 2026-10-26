/**
 * 复检：空间层级（选中节点后操作按钮）+ 组织机构社区候选。
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
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 150)))

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
  await sleep(2600)

  // 空间层级：点第一个树节点
  await page.evaluate(() => { location.hash = '#/spaces' })
  await sleep(3600)
  await page.evaluate(() => {
    const n = document.querySelector('.el-tree-node__content')
    if (n) n.click()
  })
  await sleep(1500)
  const spaces = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'))
      .map((b) => b.innerText.trim())
    return { edit: btns.includes('编辑'), del: btns.includes('删除'),
      child: btns.includes('在此节点下新增') }
  })
  console.log('空间层级按钮:', JSON.stringify(spaces))
  await page.screenshot({ path: path.join(OUT, 'fix3-spaces.png') })

  // 空间层级：打开新增，看组织/上级是否为名称
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.trim() === '新增空间')
    if (b) b.click()
  })
  await sleep(1500)
  const createForm = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    if (!dlg) return {}
    const labels = Array.from(dlg.querySelectorAll('.el-form-item__label'))
      .map((x) => x.innerText.trim())
    const inputs = Array.from(dlg.querySelectorAll('.el-select'))
      .map((s) => s.innerText.replace(/\s+/g, ' ').trim().slice(0, 30))
    return { labels, selects: inputs }
  })
  console.log('新增空间表单:', JSON.stringify(createForm).slice(0, 260))
  await page.screenshot({ path: path.join(OUT, 'fix3-space-create.png') })
  await page.keyboard.press('Escape')
  await sleep(600)

  // 组织机构：新增弹窗的社区候选
  await page.evaluate(() => { location.hash = '#/orgs' })
  await sleep(3600)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /新增组织|新增/.test(x.innerText || ''))
    if (b) b.click()
  })
  await sleep(1800)
  const orgForm = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    if (!dlg) return {}
    const labels = Array.from(dlg.querySelectorAll('.el-form-item__label'))
      .map((x) => x.innerText.trim())
    const hint = dlg.innerText.includes('区划') || dlg.innerText.includes('社区')
    return { labels: labels.slice(0, 12), hasCommunity: labels.some((l) => l.includes('社区')) , hint }
  })
  console.log('组织机构表单:', JSON.stringify(orgForm).slice(0, 240))
  await page.screenshot({ path: path.join(OUT, 'fix3-org.png') })

  await browser.close()
})()
