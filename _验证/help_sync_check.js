/**
 * 帮助页验证：本轮修正是否已写入内置帮助。
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
  await sleep(2200)

  await page.evaluate(() => { location.hash = '#/help?sec=asset' })
  await sleep(2600)

  const info = await page.evaluate(() => {
    const body = document.querySelector('.help-body') || document.body
    const txt = body.innerText
    const checks = ['在此节点下新增', '可搜索下拉', '南北通透', '床位管理',
      '本地上传', '四级（省/市/区县/街道）']
    return {
      hits: checks.map((c) => c + ':' + (txt.includes(c) ? '有' : '无')),
      scroll: (document.querySelector('.help-body') || {}).scrollTop
    }
  })
  console.log('帮助页命中:', info.hits.join(' | '))
  await page.screenshot({ path: path.join(OUT, 'help-ui-sync.png') })
  await browser.close()
})()
