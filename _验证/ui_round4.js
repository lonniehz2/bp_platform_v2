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
    if (b) b.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1500)

  await page.evaluate(() => { location.hash = '#/contracts' })
  await sleep(4000)
  console.log('发起变更入口:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('button')).filter(b => b.innerText.trim() === '发起变更').length))
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.trim() === '发起变更')
    if (b) b.click()
  })
  await sleep(900)
  console.log('变更弹窗:', await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    return d ? d.innerText.slice(0, 50).replace(/\n/g, ' | ') : null
  }))
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    const b = d && Array.from(d.querySelectorAll('button')).find(x => x.innerText === '取消')
    if (b) b.click()
  })

  await page.evaluate(() => { location.hash = '#/contract-changes' })
  await sleep(3500)
  console.log('变更表头:', JSON.stringify(await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-table__header th')).map(t => t.innerText.trim()).filter(Boolean))))
  console.log('展开后中文:', await page.evaluate(() => {
    const btn = document.querySelector('.el-table__expand-icon')
    if (btn) btn.click()
    return true
  }))
  await sleep(900)
  console.log('展开内容:', await page.evaluate(() => document.body.innerText.includes('月租金') || document.body.innerText.includes('止租日')))

  await page.evaluate(() => { location.hash = '#/bills' })
  await sleep(3500)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(x => x.innerText.includes('登记收款'))
    if (b) b.click()
  })
  await sleep(900)
  console.log('收款组织下拉:', await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find(x => x.offsetParent)
    return d ? d.querySelectorAll('.el-select').length : 0
  }))
  await browser.close()
})()
