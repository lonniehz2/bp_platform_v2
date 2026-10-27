const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const DL = path.join(__dirname, '_downloads')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
if (!fs.existsSync(DL)) fs.mkdirSync(DL)
;(async () => {
  const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await browser.newPage()
  await page.setViewport({ width: 1560, height: 1000 })
  await page.setCacheEnabled(false)
  const client = await page.createCDPSession()
  await client.send('Page.setDownloadBehavior', { behavior: 'allow', downloadPath: DL })
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

  for (const [hash, testid] of [['#/bills', 'bill-export']]) {
    await page.evaluate((h) => { location.hash = h }, hash)
    await sleep(3000)
    const btn = await page.$('[data-testid="' + testid + '"]')
    console.log(hash, '按钮存在:', !!btn)
    if (btn) {
      await btn.click()
      await sleep(25000)
      const msg = await page.evaluate(() => Array.from(document.querySelectorAll('.el-message'))
        .map((x) => x.innerText.trim()))
      console.log(hash, '提示:', JSON.stringify(msg))
    }
  }
  await sleep(2000)
  console.log('下载文件:', fs.readdirSync(DL))
  for (const f of fs.readdirSync(DL)) {
    const full = path.join(DL, f)
    const text = fs.readFileSync(full, 'utf8')
    console.log(f, '行数:', text.split(/\r?\n/).length, '首行:', text.split(/\r?\n/)[0].slice(0, 80))
  }
  await browser.close()
})()
