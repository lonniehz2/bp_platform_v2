const puppeteer = require('puppeteer-core')
const fs = require('fs')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const CASES = [
  ['#/contracts', '新建合同'], ['#/applications', '新建申请'], ['#/allocations', '新建批次'],
  ['#/houses', '新增房源'], ['#/persons', '新增人员'], ['#/terminations', '发起退租'],
  ['#/exchanges', '新建换房'], ['#/complaints', '新建投诉'], ['#/alerts', '新建告警'],
  ['#/fee-items', '新增项目'], ['#/fee-items', '新增计费规则'], ['#/arrears', '新建处置'],
  ['#/orgs', '新增组织'], ['#/spaces', '新增空间'], ['#/subsidies', '新建标准'],
  ['#/meter-readings', '录入读数']
]
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
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

  const out = []
  for (const [route, btn] of CASES) {
    await page.evaluate((r) => { location.hash = r }, route)
    await sleep(2400)
    const opened = await page.evaluate((t) => {
      const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === t)
      if (b) { b.click(); return true }
      return false
    }, btn)
    await sleep(1000)
    const hasDialog = await page.evaluate(() =>
      !!(Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)))
    let msg = ''
    if (hasDialog) {
      await page.evaluate(() => {
        const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
        const b = Array.from(d.querySelectorAll('button'))
          .find((x) => /^(提交|保存|确定|新增|创建|录入|确认)/.test(x.innerText.trim()))
        if (b) b.click()
      })
      await sleep(1400)
      msg = await page.evaluate(() =>
        Array.from(document.querySelectorAll('.el-message')).map((x) => x.innerText.trim()).join(' | '))
      await page.keyboard.press('Escape')
      await sleep(400)
    }
    out.push({ route, btn, opened, hasDialog, msg })
  }
  fs.writeFileSync(__dirname + '/_ui_validation_audit.json', JSON.stringify(out, null, 2), 'utf8')
  console.log(out.map((o) => `${o.route}\t${o.btn}\t弹窗=${o.hasDialog ? 'Y' : 'N'}\t校验=${o.msg || '(无提示)'}`).join('\n'))
  await browser.close()
})()
