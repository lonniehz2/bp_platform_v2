const fs = require('fs')
const path = require('path')
const puppeteer = require('puppeteer-core')
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

;(async () => {
  const router = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'src', 'router', 'index.js'), 'utf8')
  const routes = [...router.matchAll(/path:\s*'([^']+)'/g)].map((m) => m[1])
    .filter((p) => p.startsWith('/') && !p.includes(':') && !p.includes('platform-admin') && p !== '/login' && p !== '/help')
  const b = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
  const page = await b.newPage()
  await page.setViewport({ width: 1440, height: 900 })
  await page.setCacheEnabled(false)
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle2' })
  await page.evaluate(() => localStorage.setItem('bp_locale', 'en-US'))
  await page.reload({ waitUntil: 'networkidle2' })
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
  await page.evaluate(() => {
    const x = Array.from(document.querySelectorAll('button')).find((t) => t.innerText.includes('Sign in'))
    if (x) x.click()
  })
  await page.waitForFunction(() => !!document.querySelector('.rail'), { timeout: 30000 })
  await sleep(1200)
  const out = []
  for (const p of routes) {
    try {
      await page.goto(BASE + '/#' + p, { waitUntil: 'networkidle2', timeout: 60000 })
      await sleep(1300)
      const info = await page.evaluate(() => {
        const main = document.querySelector('.page-card') || document.querySelector('.app-main') || document.body
        const text = main.innerText || ''
        const title = main.querySelector('h1,h2,h3')?.innerText?.trim() || ''
        const chunks = [...new Set(text.match(/[\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9（）()·：:，,。./\-]*/g) || [])]
        const raw = [...new Set(text.match(/\b[a-z][a-zA-Z]+\.[a-zA-Z][a-zA-Z.]+\b/g) || [])]
        return { title, zh: (text.match(/[\u4e00-\u9fff]/g) || []).length, chunks: chunks.slice(0, 40), raw: raw.slice(0, 20) }
      })
      out.push({ path: p, ...info })
      console.log(p, 'zh=' + info.zh, 'raw=' + (info.raw.length || 0), '|', info.chunks.slice(0, 6).join(' / '))
    } catch (e) {
      console.log(p, 'ERR', String(e).slice(0, 100))
    }
  }
  fs.writeFileSync(path.join(__dirname, '_en_audit.json'), JSON.stringify(out, null, 2))
  await b.close()
})()
