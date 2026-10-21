/**
 * 全系统 UI 质量体检
 *
 * 覆盖用户反馈的四类问题中的三类（可自动判定）：
 *   ① 查询按钮点击后是否真的发起请求（页面无响应）
 *   ② 表格整列为空（内容空白）
 *   ③ 单元格出现英文编码而非中文
 * 第四类「表单缺字段」需业务判断，脚本只输出每页表单字段清单供人工核对。
 *
 * 用法：node _audit_ui_quality.js [输出 json 路径]
 */
const puppeteer = require('puppeteer-core')
const fs = require('fs')
const path = require('path')

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const BASE = 'http://192.168.31.11:8080'
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// 菜单里的业务页面（含 tab 页面仅取默认 tab，避免重复）
const ROUTES = [
  ['/dashboard', '运营驾驶舱'], ['/persons', '人员档案'], ['/applications', '申请与审核'],
  ['/houses', '房源台账'], ['/allocation', '配租与摇号'], ['/contracts', '合同管理'],
  ['/contract-changes', '合同变更'], ['/exchanges', '换房管理'], ['/terminations', '退租管理'],
  ['/bills', '账单与缴费'], ['/payments', '收款管理'], ['/deposits', '押金与退款'],
  ['/refunds', '退款管理'], ['/arrears', '催缴管理'], ['/dunnings', '催缴登记'],
  ['/fee-items', '计费项目'], ['/subsidies', '补贴管理'], ['/reconciles', '对账管理'],
  ['/cashflow', '资金流水'], ['/annual-reviews', '年度复核'], ['/guarantee', '保障档案'],
  ['/alerts', '告警管理'], ['/complaints', '投诉管理'], ['/appeals', '申诉管理'],
  ['/credits', '信用惩戒'], ['/visits', '走访记录'], ['/keyring', '钥匙包'],
  ['/devices', '设备管理'], ['/access-records', '门禁记录'], ['/workorders', '工单管理'],
  ['/messages', '消息与待办'], ['/todos', '待办中心'], ['/reports', '报表导出'],
  ['/publicities', '公示管理'], ['/gov-reports', '监管报送'], ['/waitlist', '轮候库'],
  ['/rebate', '补贴退返'], ['/insurance', '保险管理'], ['/talent', '人才安居'],
  ['/orgs', '组织机构'], ['/rbac', '用户与权限'], ['/sys', '系统支撑'], ['/ops-center', '运维操作台'],
  ['/ops-extras', '扩展操作台']
]

const EN_CODE = /^[A-Z][A-Z0-9_]{2,}$/

;(async () => {
  const browser = await puppeteer.launch({
    executablePath: EDGE, headless: 'new',
    args: ['--no-sandbox'], defaultViewport: { width: 1600, height: 1000 }
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
  await sleep(4500)

  const report = []
  for (const [route, name] of ROUTES) {
    let reqCount = 0
    const onReq = (r) => { if (r.url().includes('/api/')) reqCount++ }
    page.on('request', onReq)
    try {
      await page.goto(BASE + '/#' + route, { waitUntil: 'domcontentloaded', timeout: 30000 })
      await sleep(1400)

      // 表格体检：列名、整列为空、英文编码
      const table = await page.evaluate(() => {
        const t = document.querySelector('.el-table')
        if (!t) return null
        const heads = Array.from(t.querySelectorAll('thead th')).map((th) => (th.innerText || '').trim())
        const rows = Array.from(t.querySelectorAll('tbody tr'))
        const body = rows.slice(0, 30).map((tr) =>
          Array.from(tr.querySelectorAll('td')).map((td) => (td.innerText || '').trim()))
        return { heads, body, rowCount: rows.length }
      })

      // 表单字段清单（用于人工判断是否缺字段）
      const formFields = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('.el-form-item__label'))
          .map((l) => (l.innerText || '').trim()).filter(Boolean)
      })

      // 点击「查询」看是否发请求
      reqCount = 0
      const clicked = await page.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button'))
          .find((b) => /^\s*查\s*询\s*$/.test(b.innerText || ''))
        if (!btn) return false
        btn.click()
        return true
      })
      await sleep(1500)
      page.off('request', onReq)

      let emptyCols = []
      let enCodes = []
      if (table && table.rowCount > 0) {
        const n = table.heads.length
        for (let c = 0; c < n; c++) {
          const vals = table.body.map((r) => r[c] || '')
          const nonEmpty = vals.filter((v) => v && v !== '-').length
          if (nonEmpty === 0) emptyCols.push(table.heads[c] || ('列' + (c + 1)))
        }
        const seen = new Set()
        table.body.forEach((r) => r.forEach((v) => {
          if (EN_CODE.test(v) && !seen.has(v)) { seen.add(v); enCodes.push(v) }
        }))
      }

      report.push({
        route, name,
        hasTable: !!table,
        rowCount: table ? table.rowCount : 0,
        hasQueryBtn: clicked,
        queryFired: reqCount > 0,
        emptyCols,
        enCodes: enCodes.slice(0, 8),
        formFields: formFields.slice(0, 20)
      })
      console.log('%-16s 行=%-4d 查询=%s%s 空列=%d 英文=%d',
        name, table ? table.rowCount : 0,
        clicked ? '有' : '无', clicked ? (reqCount > 0 ? '(有请求)' : '(无请求!)') : '',
        emptyCols.length, enCodes.length)
    } catch (e) {
      report.push({ route, name, error: String(e).slice(0, 120) })
      console.log('%-16s ✗ %s', name, String(e).slice(0, 60))
      page.off('request', onReq)
    }
  }

  const out = process.argv[2] || path.join(__dirname, 'ui_quality.json')
  fs.writeFileSync(out, JSON.stringify(report, null, 2), 'utf-8')
  console.log('\n报告已写入：' + out)
  await browser.close()
})()
