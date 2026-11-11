const fs = require('node:fs')
const path = require('node:path')
const puppeteer = require('puppeteer-core')

const EDGE = process.env.EDGE_PATH || 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = process.env.PLATFORM_BASE || 'http://127.0.0.1:8091'
const sleep = ms => new Promise(r => setTimeout(r, ms))

async function run() {
  if (!fs.existsSync(EDGE)) throw new Error(`Edge not found: ${EDGE}`)
  const main = fs.readFileSync(path.resolve(__dirname, '../../platform-frontend/src/main.js'), 'utf8')
  const paths = [...new Set([...main.matchAll(/path:\s*'([^']+)'/g)].map(m => m[1]))]
    .filter(p => !p.includes(':') && !['/login', '/'].includes(p))
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await page.evaluate(() => localStorage.setItem('platformLocale', 'en-US'))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(500)
  await page.evaluate(() => {
    const inputs = [...document.querySelectorAll('.login-card input')]
    const values = ['350600', 'admin', 'admin123']
    inputs.forEach((el, i) => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, values[i])
      el.dispatchEvent(new Event('input', { bubbles: true }))
    })
  })
  await page.evaluate(() => document.querySelector('.login-submit').click())
  await page.waitForFunction(() => !!document.querySelector('.sidebar'), { timeout: 20000 })
  const bad = []
  for (const route of paths) {
    await page.goto(BASE + '/#' + route, { waitUntil: 'networkidle2' })
    await sleep(350)
    const hits = await page.evaluate(() => {
      const selectors = ['h1', '.nav-label', 'button', '.tab-btn', 'th', 'label']
      const out = []
      for (const selector of selectors) for (const el of document.querySelectorAll(selector)) {
        const text = (el.innerText || '').trim()
        if (text && /[\u4e00-\u9fa5]/.test(text) && !out.includes(text) && !/^(保障房|资产|服务)(管理员|经理|财务|客服)$/.test(text) && text !== '验证角色') out.push(text)
      }
      return out
    })
    if (hits.length) bad.push({ route, hits: hits.slice(0, 8) })
  }

  const dialogs = [
    ['/guarantee/contracts', /^New Contract$/],
    ['/guarantee/applications', /^New Application$/],
    ['/guarantee/persons', /^Edit$/],
    ['/guarantee/billing', /^Pay$/]
  ]
  for (const [route, pattern] of dialogs) {
    await page.goto(BASE + '/#' + route, { waitUntil: 'networkidle2' })
    await sleep(700)
    const clicked = await page.evaluate((source) => {
      const button = [...document.querySelectorAll('button')].find(el => new RegExp(source).test((el.innerText || '').trim()))
      if (button) { button.click(); return true }
      return false
    }, pattern.source)
    if (!clicked) { bad.push({ route, hits: [`未找到弹窗按钮 ${pattern}`] }); continue }
    await sleep(500)
    const hits = await page.evaluate(() => {
      const modal = document.querySelector('.modal')
      if (!modal) return []
      return [...modal.querySelectorAll('h2,label,button,th')].map(el => (el.innerText || '').trim()).filter(t => /[\u4e00-\u9fa5]/.test(t))
    })
    if (hits.length) bad.push({ route: route + ' [modal]', hits: [...new Set(hits)].slice(0, 8) })
    await page.keyboard.press('Escape')
    await sleep(150)
  }

  await browser.close()
  if (bad.length) {
    for (const item of bad) console.error(`[en-smoke] ${item.route}: ${item.hits.join(' | ')}`)
    process.exit(1)
  }
  console.log(`[en-smoke] 通过：${paths.length} 个路由 + ${dialogs.length} 个弹窗无中文 UI 标签`)
}
run().catch(error => { console.error(error); process.exit(1) })
