/**
 * 登录参考系统并抓取结构：菜单树、页面标题、表格列、表格样例行、截图
 *
 * 用本机 Edge（puppeteer-core 免下载浏览器），演示账号登录。
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const OUT = __dirname
const SHOT = path.join(OUT, 'shots')
if (!fs.existsSync(SHOT)) fs.mkdirSync(SHOT, { recursive: true })

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE,
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--window-size=1680,1000'],
    defaultViewport: { width: 1680, height: 1000 }
  })
  const page = await browser.newPage()
  const log = []
  const say = (s) => { console.log(s); log.push(s) }

  try {
    say('打开登录页...')
    await page.goto('https://saas.yumeng.work/', { waitUntil: 'networkidle2', timeout: 90000 })
    await sleep(3000)
    await page.screenshot({ path: path.join(SHOT, '01-login.png') })

    // 打印所有输入框，判断登录表单结构
    const inputs = await page.evaluate(() =>
      Array.from(document.querySelectorAll('input')).map((el) => ({
        type: el.type, placeholder: el.placeholder || '',
        name: el.name || '', cls: (el.className || '').slice(0, 60)
      })))
    say('输入框：' + JSON.stringify(inputs))

    // 填账号密码（按 type/placeholder 匹配）
    const phoneSel = 'input[type="text"], input[type="tel"], input:not([type])'
    await page.click(phoneSel).catch(() => {})
    await page.keyboard.type('17701311856', { delay: 40 })
    const pwd = await page.$('input[type="password"]')
    if (pwd) {
      await pwd.click()
      await page.keyboard.type('a123456', { delay: 40 })
    }
    await page.screenshot({ path: path.join(SHOT, '02-filled.png') })

    // 点登录按钮
    const clicked = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'))
      const b = btns.find((x) => /登\s*录|登录|立即登录/.test(x.innerText || ''))
      if (b) { b.click(); return b.innerText.trim() }
      return null
    })
    say('点击按钮：' + clicked)

    await sleep(6000)
    await page.screenshot({ path: path.join(SHOT, '03-after-login.png') })
    say('登录后 URL：' + page.url())

    // 抓菜单：Ant Design 菜单项
    const menu = await page.evaluate(() => {
      const out = []
      document.querySelectorAll('.ant-menu-item, .ant-menu-submenu-title').forEach((el) => {
        out.push({
          text: (el.innerText || '').trim().replace(/\s+/g, ' '),
          cls: el.className
        })
      })
      return out
    })
    say('菜单项数：' + menu.length)
    fs.writeFileSync(path.join(OUT, 'menu.json'), JSON.stringify(menu, null, 1), 'utf8')
    menu.forEach((m) => say('  · ' + m.text))

    // 抓当前页表格结构
    const table = await page.evaluate(() => {
      const th = Array.from(document.querySelectorAll('.ant-table-thead th'))
        .map((x) => (x.innerText || '').trim())
      const trs = Array.from(document.querySelectorAll('.ant-table-tbody tr')).slice(0, 3)
      const rows = trs.map((tr) =>
        Array.from(tr.querySelectorAll('td')).map((td) => (td.innerText || '').trim().slice(0, 30)))
      return { th, rows }
    })
    say('表格列：' + JSON.stringify(table.th))
    say('样例行：' + JSON.stringify(table.rows))
    fs.writeFileSync(path.join(OUT, 'table.json'), JSON.stringify(table, null, 1), 'utf8')

    // 页面整体文字（判断页面结构）
    const text = await page.evaluate(() => (document.body.innerText || '').slice(0, 3000))
    fs.writeFileSync(path.join(OUT, 'page-text.txt'), text, 'utf8')

    fs.writeFileSync(path.join(OUT, 'run.log'), log.join('\n'), 'utf8')
    say('完成')
  } catch (e) {
    say('ERROR: ' + e.message)
    try { await page.screenshot({ path: path.join(SHOT, '99-error.png') }) } catch (_) {}
    fs.writeFileSync(path.join(OUT, 'run.log'), log.join('\n'), 'utf8')
  } finally {
    await browser.close()
  }
})()
