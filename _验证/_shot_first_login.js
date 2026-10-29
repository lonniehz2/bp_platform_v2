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
  await sleep(1000)
  await page.evaluate(() => {
    const el = document.querySelectorAll('input')
    const set = (i, v) => { el[i].focus(); el[i].value = v
      el[i].dispatchEvent(new Event('input', { bubbles: true }))
      el[i].dispatchEvent(new Event('change', { bubbles: true })); el[i].blur() }
    set(0, '350698001'); set(1, 'firstadmin'); set(2, 'BpKDdABvqXT$')
  })
  await sleep(300)
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('登'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(2000)
  console.log('forced dialog:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-dialog')).some((d) => d.offsetParent &&
      d.innerText.includes('修改初始密码'))))
  await page.screenshot({ path: '_验证/first_login_pwd.png' })

  // 填写并保存
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const ins = d.querySelectorAll('input')
    const set = (i, v) => { ins[i].focus(); ins[i].value = v
      ins[i].dispatchEvent(new Event('input', { bubbles: true }))
      ins[i].dispatchEvent(new Event('change', { bubbles: true })); ins[i].blur() }
    set(0, 'BpKDdABvqXT$'); set(1, 'NewPass@12345'); set(2, 'NewPass@12345')
  })
  await sleep(300)
  await page.evaluate(() => {
    const d = Array.from(document.querySelectorAll('.el-dialog')).find((x) => x.offsetParent)
    const btn = Array.from(d.querySelectorAll('button')).find((x) => x.innerText.includes('保存并继续'))
    if (btn) btn.click()
  })
  await sleep(1500)
  console.log('after change dialog:', await page.evaluate(() =>
    Array.from(document.querySelectorAll('.el-dialog')).some((d) => d.offsetParent &&
      d.innerText.includes('修改初始密码'))))

  // 平台信息页
  await page.evaluate(() => { location.hash = '#/platform-info' })
  await sleep(2500)
  console.log('platform info:', await page.evaluate(() => {
    const t = document.body.innerText
    return { hasPage: t.includes('平台信息'), codeDisabled: !!document.querySelector('input[disabled]') }
  }))
  await page.screenshot({ path: '_验证/platform_info.png' })
  await b.close()
})()
