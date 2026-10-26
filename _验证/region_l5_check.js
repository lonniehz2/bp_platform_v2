/**
 * 五级地址验证：组织机构新增弹窗能选到「街道 → 社区」。
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

  await page.evaluate(() => { location.hash = '#/orgs' })
  await sleep(3000)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /新增组织/.test(x.innerText || ''))
    if (b) b.click()
  })
  await sleep(1600)

  // 打开级联选择器
  const hasCascader = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    const c = dlg?.querySelector('.el-cascader')
    if (!c) return false
    c.querySelector('input')?.click()
    return true
  })
  await sleep(1500)

  // 逐级选择：北京市 → 市辖区 → 东城区 → 东华门街道
  const steps = ['北京市', '市辖区', '东城区', '东华门街道']
  const picked = []
  for (const label of steps) {
    const ok = await page.evaluate((txt) => {
      const nodes = Array.from(document.querySelectorAll('.el-cascader-node'))
      const hit = nodes.find((n) => n.innerText.trim().startsWith(txt))
      if (hit) {
        const radio = hit.querySelector('.el-radio, input[type="radio"]')
        if (radio) radio.click()
        else hit.click()
        return true
      }
      return false
    }, label)
    picked.push(label + ':' + (ok ? '✓' : '✗'))
    await sleep(1400)
  }

  // 街道展开后，是否出现第五级（社区）
  const level5 = await page.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.el-cascader-node'))
      .map((n) => n.innerText.trim()).filter(Boolean)
    const comm = nodes.filter((t) => t.includes('社区') || t.includes('居委会') || t.includes('村'))
    return { total: nodes.length, sample: nodes.slice(-5), communityCount: comm.length,
      firstCommunity: comm[0] || '' }
  })
  console.log('级联逐级选择:', picked.join(' '))
  console.log('第五级候选:', JSON.stringify(level5).slice(0, 200))
  await page.screenshot({ path: path.join(OUT, 'region-level5.png') })

  await browser.close()
})()
