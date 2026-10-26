/**
 * 验证：模板含可选值说明行；非法用途被拦下并提示可选值。
 */
const fs = require('fs')
const path = require('path')
const puppeteer = require('puppeteer-core')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const OUT = path.join(__dirname, '_shots')
const TMP = path.join(__dirname, '_tmp2')
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  fs.mkdirSync(TMP, { recursive: true })
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

  const client = await page.target().createCDPSession()
  await client.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: TMP })

  await page.evaluate(() => { location.hash = '#/houses' })
  await sleep(2600)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('批量导入'))
    if (b) b.click()
  })
  await sleep(1000)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('下载模板'))
    if (b) b.click()
  })
  await sleep(2200)

  const files = fs.readdirSync(TMP).filter((f) => f.endsWith('.csv'))
  console.log('下载文件:', files.join(','))
  let content = ''
  if (files.length) {
    content = fs.readFileSync(path.join(TMP, files[0]), 'utf8')
    console.log('模板前 3 行:')
    content.replace(/\r/g, '').split('\n').slice(0, 3).forEach((l) => console.log('  ' + l))
  }

  // 构造一行非法用途，验证逐行拦截
  const bad = '\ufeff组织编码,空间编码,房源编号,房源名称,房源类型,用途,建筑面积(㎡),租金标准,计价单位,房源状态\n'
    + '# 说明行会被跳过\n'
    + 'DEMO-P1,P1-R1,BAD' + Date.now().toString().slice(-6) + ',测试房,公租房,办公,50,10,元/㎡·月,空置\n'
  const badPath = path.join(TMP, 'bad.csv')
  fs.writeFileSync(badPath, bad, 'utf8')

  const input = await page.$('input[type=file]')
  if (input) await input.uploadFile(badPath)
  await sleep(800)
  await page.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button'))
      .find((x) => x.innerText.includes('开始导入'))
    if (b) b.click()
  })
  await sleep(2600)
  const res = await page.evaluate(() => {
    const dlg = Array.from(document.querySelectorAll('.el-dialog'))
      .find((d) => d.getBoundingClientRect().height > 0)
    return dlg ? dlg.innerText.replace(/\s+/g, ' ') : ''
  })
  console.log('非法值导入结果:', res.slice(0, 260))
  await page.screenshot({ path: path.join(OUT, 'import-constraint.png') })

  await browser.close()
})()
