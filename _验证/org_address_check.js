/**
 * 组织编辑弹窗标准地址 + 详情标准地址 校验。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'

const clickText = (page, text) => page.evaluate((t) => {
  const b = Array.from(document.querySelectorAll('button'))
    .find((x) => x.innerText.trim() === t)
  if (b) { b.click(); return true }
  return false
}, text)

const lastDialog = (page) => page.evaluate(() => {
  const d = Array.from(document.querySelectorAll('.el-dialog')).pop()
  return d ? d.innerText.replace(/\n+/g, ' | ').slice(0, 220) : '无弹窗'
})

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
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
  await new Promise(r => setTimeout(r, 300))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail, .el-menu, .aside'),
    { timeout: 20000 })

  await page.goto(BASE + '/#/orgs', { waitUntil: 'networkidle2' })
  await new Promise(r => setTimeout(r, 2500))

  console.log('详情:', await clickText(page, '详情'),
    (await new Promise(r => setTimeout(r, 900)), await lastDialog(page)))
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog__headerbtn')).pop()
    d && d.click()
  })
  await new Promise(r => setTimeout(r, 600))

  console.log('编辑:', await clickText(page, '编辑'),
    (await new Promise(r => setTimeout(r, 900)), await lastDialog(page)))

  // 点开编辑弹窗里的标准地址级联
  const picked = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog')).pop()
    if (!dlg) return false
    const inp = Array.from(dlg.querySelectorAll('input'))
      .find((i) => (i.placeholder || '').includes('省'))
    if (!inp) return false
    inp.click()
    return true
  })
  await new Promise(r => setTimeout(r, 1600))
  const nodes = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-cascader-node__label'))
      .map((x) => x.innerText.trim()).slice(0, 5))
  console.log('编辑内地址级联:', picked, nodes.join(' / ') || '（空）')
  await page.screenshot({ path: path.join(__dirname, '_shots', 'fix-org-edit-address.png') })

  await browser.close()
})()
