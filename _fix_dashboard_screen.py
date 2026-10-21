# -*- coding: utf-8 -*-
"""修复：①指标编码显示中文 ②大屏图表可靠渲染"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 指标中文名常量 ----------
CONST = '''/**
 * 指标编码 → 中文名称。
 * 编码来源：后端 MetricServiceImpl（13 个指标）。
 * 前端只做展示映射，不参与计算。
 */
export const METRIC_LABEL = {
  HOUSE_TOTAL: '房源总数',
  HOUSE_OCCUPIED: '已租房源',
  HOUSE_VACANT: '空置房源',
  OCCUPANCY_RATE: '出租率',
  BILL_UNPAID_AMOUNT: '欠费金额',
  BILL_UNPAID_COUNT: '欠费账单数',
  PAYMENT_TOTAL_AMOUNT: '累计收款',
  ACCESS_TODAY_COUNT: '今日开门',
  ACCESS_ABNORMAL_COUNT: '今日异常开门',
  ALLOCATED: '已配租',
  PENDING_ALLOC: '待配租',
  OCCUPIED: '占用',
  VACANT: '空置'
}

/** 图表类型 → 中文（大屏/驾驶舱卡片副标题用） */
export const CHART_LABEL = {
  NUMBER: '数值',
  GAUGE: '仪表盘',
  LINE: '折线',
  BAR: '柱状',
  PIE: '饼图'
}

/** 单位 */
export const METRIC_UNIT = {
  OCCUPANCY_RATE: '%',
  BILL_UNPAID_AMOUNT: '元',
  PAYMENT_TOTAL_AMOUNT: '元'
}

export function metricLabel(code) {
  return METRIC_LABEL[code] || code
}

export function chartLabel(type) {
  return CHART_LABEL[type] || type || ''
}

export function metricUnit(code) {
  return METRIC_UNIT[code] || ''
}
'''
os.makedirs(os.path.join(FE, 'constants'), exist_ok=True)
io.open(os.path.join(FE, 'constants', 'metrics.js'), 'w',
        encoding='utf-8').write(CONST)
print('  ✓ 新建 constants/metrics.js（13 个指标中文名）')

# ---------- 2) Dashboard：中文名 + 单位 ----------
D = os.path.join(FE, 'views', 'Dashboard.vue')
s = io.open(D, encoding='utf-8').read()

s = s.replace('<div class="muted">{{ w.chart }}</div>',
              '<div class="muted">{{ w.chartLabel }}</div>')
s = s.replace('''        <el-table-column prop="code" label="指标编码" width="240" />
        <el-table-column prop="value" label="当前值" />''',
              '''        <el-table-column prop="label" label="指标名称" width="170" />
        <el-table-column prop="code" label="编码" width="230" />
        <el-table-column prop="value" label="当前值" />''')

s = s.replace("import { rptApi } from '@/api/modules'",
              "import { rptApi } from '@/api/modules'\n"
              "import { metricLabel, chartLabel, metricUnit } from '@/constants/metrics'")

s = s.replace('''const UNITS = {
  OCCUPANCY_RATE: '%', BILL_UNPAID_AMOUNT: '元', PAYMENT_TOTAL_AMOUNT: '元'
}''', '')

s = s.replace('''    widgets.value = (data.widgets || []).map((w) => ({
      ...w,
      title: w.title + (UNITS[w.code] ? `（${UNITS[w.code]}）` : '')
    }))''',
              '''    widgets.value = (data.widgets || []).map((w) => {
      const unit = metricUnit(w.code)
      return {
        ...w,
        // 后端返回的 title 若为空或等于编码，则用中文映射兜底
        title: (!w.title || w.title === w.code ? metricLabel(w.code) : w.title)
          + (unit ? `（${unit}）` : ''),
        chartLabel: chartLabel(w.chart)
      }
    })''')

s = s.replace('''    .map(([code, value]) => ({ code, value: fmt(value) }))''',
              '''    .map(([code, value]) => ({
      code, label: metricLabel(code), value: fmt(value)
    }))''')

io.open(D, 'w', encoding='utf-8').write(s)
print('  ✓ Dashboard.vue：指标明细加中文名称，卡片副标题显示中文图表类型')

# ---------- 3) ScreenApp：先建图后取数 + 中文兜底 ----------
S = os.path.join(FE, 'screen', 'ScreenApp.vue')
t = io.open(S, encoding='utf-8').read()

t = t.replace("import { rptApi } from '@/api/modules'",
              "import { rptApi } from '@/api/modules'\n"
              "import { metricLabel, metricUnit } from '@/constants/metrics'")

t = t.replace("const UNITS = { OCCUPANCY_RATE: '%', BILL_UNPAID_AMOUNT: '元', PAYMENT_TOTAL_AMOUNT: '元' }",
              "")

t = t.replace('''const kpis = computed(() => (widgets.value || []).slice(0, 4).map((w) => ({
  code: w.code,
  title: w.title,''',
              '''const kpis = computed(() => (widgets.value || []).slice(0, 4).map((w) => ({
  code: w.code,
  title: (!w.title || w.title === w.code) ? metricLabel(w.code) : w.title,''')

t = t.replace("  unit: UNITS[w.code] || '',", "  unit: metricUnit(w.code),")

# 初始化提前 + 尺寸兜底 + 观测器
t = t.replace('''onMounted(async () => {
  tickClock()
  clockTimer = setInterval(tickClock, 1000)
  await load()
  timer = setInterval(load, Math.max(15, refreshSeconds.value) * 1000)
})''',
              '''onMounted(async () => {
  tickClock()
  clockTimer = setInterval(tickClock, 1000)
  // 先建图（此时容器已有尺寸），再取数据；避免取数失败导致空白
  await nextTick()
  initCharts()
  renderCharts()
  // 容器尺寸变化（侧边栏折叠/缩放）时确保图表跟随
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => resize())
    ;[pieRef.value, barRef.value, moneyRef.value].forEach((el) => el && ro.observe(el))
    charts._ro = ro
  }
  await load()
  timer = setInterval(load, Math.max(15, refreshSeconds.value) * 1000)
})''')

# 取数失败也重绘（保持框架可见）
t = t.replace('''  } catch (e) {
    error.value = '数据加载失败（需登录且后端可达）'
  }''',
              '''  } catch (e) {
    error.value = '数据加载失败：请确认已登录且后端可达后点「刷新」'
    // 仍渲染图表框架，避免整屏空白
    if (charts.pie) renderCharts()
  }''')

# initCharts 幂等 + 尺寸为 0 时兜底重试
t = t.replace('''function initCharts() {
  charts.pie = echarts.init(pieRef.value)
  charts.bar = echarts.init(barRef.value)
  charts.money = echarts.init(moneyRef.value)
  window.addEventListener('resize', resize)
}''',
              '''function initCharts() {
  if (charts.pie) return
  charts.pie = echarts.init(pieRef.value || undefined)
  charts.bar = echarts.init(barRef.value || undefined)
  charts.money = echarts.init(moneyRef.value || undefined)
  window.addEventListener('resize', resize)
  // 某些浏览器首帧容器高度为 0，下一帧再校正一次
  requestAnimationFrame(() => resize())
}''')

io.open(S, 'w', encoding='utf-8').write(t)
print('  ✓ ScreenApp.vue：先建图后取数 + ResizeObserver + 失败仍绘框架')

# ---------- 4) CSS：给图表最小高度，防止 flex 塌陷 ----------
C = os.path.join(FE, 'screen', 'screen.css')
c = io.open(C, encoding='utf-8').read()
if 'min-height: 220px' not in c:
    c = c.replace('.chart { flex: 1; min-height: 0; }',
                  '.chart { flex: 1; min-height: 220px; width: 100%; }')
    io.open(C, 'w', encoding='utf-8').write(c)
    print('  ✓ screen.css：.chart 增加 min-height 220px')
