/**
 * 诊断：登录请求与首个业务请求的响应码，定位 401 来源。
 */
const puppeteer = require('puppeteer-core')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)

  page.on('response', async (r) => {
    const u = r.url()
    if (u.includes('/auth/login') || u.includes('/orgs') || u.includes('/rbac')) {
      let body = ''
      try { body = (await r.text()).slice(0, 120) } catch (e) { }
      console.log('NET', r.status(), u.replace(BASE, '').slice(0, 60), body.replace(/\s+/g, ' ').slice(0, 80))
    }
  })

  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(800)
  const inputs = await page.evaluate(() =>
    Array.from(document.querySelectorAll('input')).map((i) => ({
      ph: i.placeholder, type: i.type, val: i.value
    })))
  console.log('输入框:', JSON.stringify(inputs))

  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => {
      if (!el[i]) return
      el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true }))
      el[i].blur()
    }
    set(0, '350600'); set(1, 'admin'); set(2, 'admin123')
  })
  await sleep(400)
  const clicked = await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => /登\s*录/.test(x.innerText || ''))
    if (b) { b.click(); return true }
    return false
  })
  console.log('点击登录:', clicked)
  await sleep(3000)

  console.log('当前路由:', await page.evaluate(() => location.hash))
  console.log('存储键:', await page.evaluate(() => Object.keys(localStorage).join(',')))
  console.log('session 键:', await page.evaluate(() => Object.keys(sessionStorage).join(',')))
  console.log('页面片段:', await page.evaluate(() => document.body.innerText.slice(0, 80).replace(/\n+/g, ' ')))

  await browser.close()
})()
