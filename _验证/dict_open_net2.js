/**
 * 数据字典 / 开放平台：点击启停并读取提示文字，定位失败原因。
 */
const puppeteer = require('puppeteer-core')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

async function login(page) {
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await sleep(700)
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
  await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
}

const toastText = (page) => page.evaluate(() =>
  Array.from(document.querySelectorAll('.el-message')).map((m) => m.innerText.trim()))

;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1500, height: 1000 })
  await page.setCacheEnabled(false)
  page.on('response', async (r) => { if (r.url().includes('/status') || r.url().includes('/open/apps')) { let b=''; try { b = (await r.text()).slice(0,120) } catch(e){} console.log('STATUS', r.status(), r.url().slice(-40), b) } })
  page.on('pageerror', (e) => console.log('异常:', String(e).slice(0, 150)))
  await login(page)

  for (const [url, label] of [['/#/sys/dict', '数据字典'], ['/#/open', '开放平台']]) {
    await page.goto(BASE + url, { waitUntil: 'networkidle2' })
    await page.waitForSelector('.el-table__body tr', { timeout: 30000 })
    await sleep(1500)
    const clicked = await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button'))
        .find((x) => ['停用', '启用'].includes((x.innerText || '').trim()))
      if (!b) return ''
      const t = (b.innerText || '').trim()
      b.click()
      return t
    })
    await sleep(1500)
    console.log('--- 操作后 ---'); console.log(label, '点击:', clicked, '提示:', JSON.stringify(await toastText(page)))
    const back = await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button'))
        .find((x) => ['停用', '启用'].includes((x.innerText || '').trim()))
      if (!b) return ''
      const t = (b.innerText || '').trim()
      b.click()
      return t
    })
    await sleep(1400)
    console.log(label, '回切:', back, '提示:', JSON.stringify(await toastText(page)))
  }

  await browser.close()
})()
