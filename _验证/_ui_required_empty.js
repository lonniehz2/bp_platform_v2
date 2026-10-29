const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const CASES = [
  ['#/contracts', '新建合同'], ['#/applications', '新建申请'], ['#/allocations', '新建批次'],
  ['#/houses', '新增房源'], ['#/persons', '新增人员'], ['#/terminations', '发起退租'],
  ['#/exchanges', '新建换房'], ['#/complaints', '新建投诉'], ['#/alerts', '新建告警'],
  ['#/fee-items', '新增项目'], ['#/fee-items', '新增计费规则'], ['#/arrears', '新建处置'],
  ['#/orgs', '新增组织'], ['#/spaces', '新增空间'], ['#/subsidies', '新建标准'],
  ['#/meter-readings', '录入读数'], ['#/devices', '批量导入'], ['#/houses', '批量导入']
]
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1440, height: 900 })
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
  for (const [route, btn] of CASES) {
    await page.evaluate((r) => { location.hash = r }, route)
    await sleep(2300)
    await page.evaluate((t) => {
      const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.trim() === t)
      if (b) b.click()
    }, btn)
    await sleep(900)
    const info = await page.evaluate(() => {
      const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
      if (!d) return null
      const req = Array.from(d.querySelectorAll('.el-form-item.is-required'))
      const empty = req.filter((it) => {
        const inp = it.querySelector('input')
        const sel = it.querySelector('.el-select__selected-item, .el-select__placeholder')
        if (inp && inp.value) return false
        if (sel && sel.innerText.trim() && sel.innerText.trim() !== '请选择') return false
        return true
      }).map((it) => (it.querySelector('.el-form-item__label') || {}).innerText || '?')
      return { required: req.length, empty: empty.length, names: empty.slice(0, 8) }
    })
    console.log(`${route}\t${btn}\t必填${info?.required ?? '-'}\t为空${info?.empty ?? '-'}\t${(info?.names || []).join('/')}`)
    await page.keyboard.press('Escape')
    await sleep(300)
  }
  await browser.close()
})()
