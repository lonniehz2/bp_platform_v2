/**
 * 定向复检：空间层级按钮 / 日房态房源下拉 / 房源详情中文。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox', '--disable-cache'] })
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

  // 1) 空间层级
  await page.evaluate(() => { location.hash = '#/spaces' })
  await sleep(3500)
  const spaces = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'))
      .map((b) => b.innerText.trim())
    return { edit: btns.includes('编辑'), del: btns.includes('删除'),
      child: btns.includes('在此节点下新增'), title: document.querySelector('.page-card h3')?.innerText }
  })
  console.log('空间层级:', JSON.stringify(spaces))
  await page.screenshot({ path: path.join(OUT, 'fix2-spaces.png') })

  // 2) 日房态
  await page.evaluate(() => { location.hash = '#/house-calendar' })
  await sleep(3500)
  const cal = await page.evaluate(() => {
    const box = document.querySelector('.page-card .toolbar')
    const txt = box ? box.innerText.replace(/\s+/g, ' ').slice(0, 120) : ''
    const sel = document.querySelector('.el-select')
    return { toolbar: txt, hasSelect: !!sel }
  })
  console.log('日房态:', JSON.stringify(cal))
  await page.screenshot({ path: path.join(OUT, 'fix2-calendar.png') })

  // 3) 房源详情
  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(3200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('.el-table__body button'))
      .find((x) => x.innerText.trim() === '详情')
    if (b) b.click()
  })
  await sleep(2200)
  const detail = await page.evaluate(() => {
    const drawer = document.querySelector('.el-drawer')
    const txt = drawer ? drawer.innerText.replace(/\s+/g, ' ') : ''
    const grab = (k) => {
      const i = txt.indexOf(k)
      return i < 0 ? k + ':无' : txt.slice(i, i + 22)
    }
    return ['朝向', '租金单位', '计量模式'].map(grab)
  })
  console.log('房源详情:', detail.join(' | '))
  await page.screenshot({ path: path.join(OUT, 'fix2-house-detail.png') })

  await browser.close()
})()
