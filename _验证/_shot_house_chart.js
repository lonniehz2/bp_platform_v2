/**
 * 截取「房源结构」卡片，用于人工核对标签与配色
 * 用法：node _shot_house_chart.js
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'], defaultViewport: { width: 1500, height: 1000 }
  })
  const page = await browser.newPage()
  await page.goto(BASE + '/', { waitUntil: 'networkidle2', timeout: 60000 })
  await sleep(1200)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find((x) => /登\s*录/.test(x.innerText || ''))
    b && b.click()
  })
  await sleep(5000)

  const handle = await page.evaluateHandle(() => {
    const cards = Array.from(document.querySelectorAll('.stat-card'))
    return cards.find((c) => (c.innerText || '').includes('房源结构')) || cards[0]
  })
  const el = handle.asElement()
  if (el) {
    await el.screenshot({ path: path.join(__dirname, 'dash-house.png') })
    const text = await page.evaluate((node) => (node.innerText || '').replace(/\s+/g, ' '), el)
    console.log('卡片文本：' + text.slice(0, 200))
    console.log('截图已保存：dash-house.png')
  } else {
    console.log('未找到房源结构卡片')
  }
  await browser.close()
})()
