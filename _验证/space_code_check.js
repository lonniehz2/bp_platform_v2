/**
 * 验证：新增空间时「空间编码」按上级编码预填；重复时提示。
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
  await sleep(2400)

  await page.evaluate(() => { location.hash = '#/spaces' })
  await sleep(3400)

  // 选中一个节点（楼栋/单元），再点「在此节点下新增」
  const picked = await page.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.el-tree-node__content'))
    // 选第 2 个节点（通常是楼栋或单元）
    const n = nodes[1] || nodes[0]
    if (!n) return ''
    n.click()
    return n.innerText.replace(/\s+/g, ' ').trim()
  })
  await sleep(1200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('在此节点下新增'))
    if (b) b.click()
  })
  await sleep(1500)

  const filled = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    if (!dlg) return {}
    const items = Array.from(dlg.querySelectorAll('.el-form-item'))
    const codeItem = items.find((it) => it.innerText.includes('空间编码'))
    const input = codeItem?.querySelector('input')
    return {
      code: input?.value,
      hint: codeItem ? codeItem.innerText.replace(/\s+/g, ' ').slice(0, 120) : ''
    }
  })
  console.log('选中节点:', picked)
  console.log('弹窗预填:', JSON.stringify(filled).slice(0, 200))
  await page.screenshot({ path: path.join(OUT, 'space-code-prefix.png') })

  // 输入一个已存在的编码，失焦触发查重
  const dup = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    const items = Array.from(dlg.querySelectorAll('.el-form-item'))
    const codeItem = items.find((it) => it.innerText.includes('空间编码'))
    const input = codeItem?.querySelector('input')
    if (!input) return ''
    input.focus()
    input.value = 'DEMO-B1'   // 当前组织里已存在的楼栋编码
    input.dispatchEvent(new Event('input', { bubbles: true }))
    input.blur()
    return input.value
  })
  await sleep(1200)
  const msg = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    const err = dlg?.querySelector('.el-form-item__error')
    return err ? err.innerText.trim() : ''
  })
  console.log('重复编码输入:', dup, '→ 提示:', msg || '（未出现提示）')
  await page.screenshot({ path: path.join(OUT, 'space-code-dup.png') })

  await browser.close()
})()
