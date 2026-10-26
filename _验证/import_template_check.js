/**
 * 房源导入：模板中文表头 + 中文值能否导入成功。
 */
const fs = require('fs')
const path = require('path')
const puppeteer = require('puppeteer-core')

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

  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(2800)

  // 抓下载的模板内容
  const client = await page.target().createCDPSession()
  await client.send('Browser.setDownloadBehavior', {
    behavior: 'allow', downloadPath: path.join(__dirname, '_tmp')
  })
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('批量导入'))
    if (b) b.click()
  })
  await sleep(1200)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('下载模板'))
    if (b) b.click()
  })
  await sleep(2000)

  const dir = path.join(__dirname, '_tmp')
  const files = fs.existsSync(dir) ? fs.readdirSync(dir) : []
  const csv = files.find((f) => f.endsWith('.csv'))
  let content = ''
  if (csv) {
    content = fs.readFileSync(path.join(dir, csv), 'utf8')
    console.log('模板文件:', csv)
    console.log('模板内容:')
    console.log(content.replace(/\r/g, ''))
  } else {
    console.log('未捕获到下载文件:', files.join(','))
  }

  // 用模板里的第 2 行示例改一个唯一编号，走页面导入
  let testCode = ''
  if (content) {
    const lines = content.replace(/\r/g, '').split('\n').filter(Boolean)
    testCode = 'IMP' + Date.now().toString().slice(-8)
    const body = lines[0] + '\n' + lines[1].replace('HOUSE-001', testCode)
    const p = path.join(__dirname, '_tmp', 'test-import.csv')
    fs.writeFileSync(p, '\ufeff' + body + '\n', 'utf8')

    const input = await page.$('input[type=file]')
    if (input) await input.uploadFile(p)
    await sleep(900)
    await page.evaluate(() => {
      const b = Array.from(document.querySelectorAll('button'))
        .find((x) => x.innerText.includes('开始导入'))
      if (b) b.click()
    })
    await sleep(3000)
    const res = await page.evaluate(() => {
      const dlg = Array.from(document.querySelectorAll('.el-dialog'))
        .find((d) => d.getBoundingClientRect().height > 0)
      return dlg ? dlg.innerText.replace(/\s+/g, ' ').slice(0, 220) : ''
    })
    console.log('导入结果:', res)
    await page.screenshot({ path: path.join(OUT, 'import-template-cn.png') })
  }

  await browser.close()
})()
