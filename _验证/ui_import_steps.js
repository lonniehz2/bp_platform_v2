const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const csv = path.join(__dirname, '_import_sample.csv')
  fs.writeFileSync(csv, '组织编码,空间编码,房源编号,房源名称,房源类型,用途,建筑面积,租金标准,计价单位,房源状态\n'
    + 'DEMO,,ZZ-IMP-001,导入测试1,公租房,民用,45,15,元/㎡·月,空置\n'
    + 'DEMO,,ZZ-IMP-002,导入测试2,公租房,民用,50,15,元/㎡·月,空置\n'
    + 'DEMO,,ZZ-IMP-001,重复编号,公租房,民用,50,15,元/㎡·月,空置\n', 'utf8')

  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1000 })
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
  await sleep(2200)
  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(3200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes('批量导入'))
    if (b) b.click()
  })
  await sleep(1500)
  const input = await page.$('.el-dialog input[type=file]')
  if (input) await input.uploadFile(csv)
  await sleep(2000)
  const info = await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    return {
      steps: Array.from(d.querySelectorAll('.el-step__title')).map((x) => x.innerText.trim()),
      alerts: Array.from(d.querySelectorAll('.el-alert__title')).map((x) => x.innerText.trim()),
      previewRows: d.querySelectorAll('.el-table__body tr').length
    }
  })
  console.log('导入弹窗:', JSON.stringify(info))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'house-import-steps.png') })
  await browser.close()
})()
