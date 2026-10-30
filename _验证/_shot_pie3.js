const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
;(async () => {
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
  await page.evaluate(() => localStorage.setItem('bp.ui.mode', 'light'))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(800)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(300)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('登'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(3500)
  await page.screenshot({ path: '_验证/pie_light.png' })
  console.log('chart:', await page.evaluate(() => {
    const el = document.querySelector('.chart')
    const c = el && el.querySelector('canvas')
    return { w: el?.clientWidth, h: el?.clientHeight, canvas: c ? [c.width, c.height] : null, html: el?.innerHTML.slice(0, 80) }
  }))
  console.log('legend:', await page.evaluate(() => {
    const l = document.querySelector('.pie-legend')
    return l ? l.innerText.replace(/\n/g, ' | ') : null
  }))
  // dark
  await page.evaluate(() => localStorage.setItem('bp.ui.mode', 'dark'))
  await page.reload({ waitUntil: 'networkidle2' })
  await sleep(3500)
  await page.screenshot({ path: '_验证/pie_dark.png' })
  await b.close()
})()
