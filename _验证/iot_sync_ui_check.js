// 设备页「同步设备」与抄表页「从 IoT 拉取」按钮验证
const puppeteer = require('puppeteer-core')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1100 })
  await page.setCacheEnabled(false)
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 160)))

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

  const clickByText = async (hash, text, wait) => {
    await page.evaluate((h) => { location.hash = h }, hash)
    await sleep(wait)
    const found = await page.evaluate((t) => {
      const b = Array.from(document.querySelectorAll('button')).find((x) => x.innerText.includes(t))
      if (b) { b.click(); return true }
      return false
    }, text)
    return found
  }

  const devices = await page.evaluate(() => Array.from(document.querySelectorAll('button'))
    .map((b) => b.innerText.trim()).filter(Boolean).slice(0, 12))
  await page.evaluate(() => { location.hash = '#/devices' })
  await sleep(3000)
  const devBtns = await page.evaluate(() => Array.from(document.querySelectorAll('.toolbar button'))
    .map((b) => b.innerText.trim()))
  console.log('设备页按钮:', devBtns.join(' | '))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'devices-sync.png') })

  await page.evaluate(() => { location.hash = '#/meter-readings' })
  await sleep(3000)
  const meterBtns = await page.evaluate(() => Array.from(document.querySelectorAll('.toolbar button'))
    .map((b) => b.innerText.trim()))
  console.log('抄表页按钮:', meterBtns.join(' | '))
  await page.screenshot({ path: path.join(__dirname, '_shots', 'meter-pull.png') })

  await browser.close()
})()
