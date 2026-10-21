# -*- coding: utf-8 -*-
"""生成独立全屏大屏入口（ECharts，第三入口 screen.html）"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

F['view-screen.html'] = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>住房保障运营大屏</title>
</head>
<body style="margin:0;background:#050d1a">
  <div id="screen"></div>
  <script type="module" src="/src/screen/main.js"></script>
</body>
</html>
'''

F['src/screen/main.js'] = '''import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import ScreenApp from './ScreenApp.vue'
import './screen.css'

const app = createApp(ScreenApp)
app.use(createPinia())
app.use(ElementPlus, { locale: zhCn })
app.mount('#screen')
'''

F['src/screen/screen.css'] = '''* { box-sizing: border-box; }
html, body, #screen { height: 100%; margin: 0; }
body {
  background: #050d1a;
  color: #d6e4ff;
  font-family: -apple-system, BlinkMacSystemFont, 'Microsoft YaHei', sans-serif;
  overflow: hidden;
}
.screen-wrap {
  width: 100vw; height: 100vh;
  display: flex; flex-direction: column;
  padding: 12px;
  gap: 10px;
  background:
    radial-gradient(1200px 500px at 50% -10%, rgba(31,111,235,.28), transparent 70%),
    #050d1a;
}
.screen-head {
  height: 56px; display: flex; align-items: center; gap: 14px;
  border-bottom: 1px solid rgba(64,158,255,.25);
}
.screen-head h1 {
  margin: 0; font-size: 22px; letter-spacing: 3px;
  background: linear-gradient(90deg, #6db3ff, #a8e0ff);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.screen-head .spacer { flex: 1; }
.screen-head .clock { font-size: 13px; color: #7aa2d6; font-variant-numeric: tabular-nums; }
.screen-body { flex: 1; display: grid; grid-template-columns: 1fr; gap: 10px; min-height: 0; }
.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.kpi {
  position: relative;
  background: linear-gradient(180deg, rgba(31,111,235,.18), rgba(31,111,235,.05));
  border: 1px solid rgba(64,158,255,.28);
  border-radius: 8px;
  padding: 12px 14px;
}
.kpi .label { font-size: 13px; color: #8fb8e8; }
.kpi .value { font-size: 30px; font-weight: 700; margin-top: 6px;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 18px rgba(109,179,255,.45); }
.kpi .unit { font-size: 13px; color: #8fb8e8; margin-left: 4px; }
.kpi.warn .value { color: #ffc53d; }
.kpi.danger .value { color: #ff7875; }
.kpi.ok .value { color: #73d13d; }
.charts { flex: 1; display: grid; grid-template-columns: 1.1fr 1fr 1fr; gap: 10px; min-height: 0; }
.panel {
  background: rgba(13,28,52,.72);
  border: 1px solid rgba(64,158,255,.22);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex; flex-direction: column; min-height: 0;
}
.panel .title { font-size: 14px; color: #9fc6f5; margin-bottom: 6px; }
.chart { flex: 1; min-height: 0; }
.screen-foot { height: 26px; display: flex; align-items: center; gap: 14px;
  font-size: 12px; color: #5c86b8; border-top: 1px solid rgba(64,158,255,.15); }
'''

F['src/screen/ScreenApp.vue'] = '''<template>
  <div class="screen-wrap">
    <div class="screen-head">
      <h1>租赁性保障用房运营大屏</h1>
      <el-tag size="small" style="background:transparent;color:#6db3ff;border-color:#2a5b96">
        {{ screenName }}
      </el-tag>
      <div class="spacer" />
      <span class="clock">{{ clock }}</span>
      <el-button size="small" type="primary" plain @click="load">刷新</el-button>
    </div>

    <div class="screen-body">
      <div class="kpi-row">
        <div v-for="w in kpis" :key="w.code" :class="['kpi', w.tone]">
          <div class="label">{{ w.title }}</div>
          <div class="value">
            {{ w.value }}<span class="unit">{{ w.unit }}</span>
          </div>
        </div>
      </div>

      <div class="charts">
        <div class="panel">
          <div class="title">房源状态结构</div>
          <div ref="pieRef" class="chart" />
        </div>
        <div class="panel">
          <div class="title">开门与异常趋势（今日）</div>
          <div ref="barRef" class="chart" />
        </div>
        <div class="panel">
          <div class="title">欠费与收款对比</div>
          <div ref="moneyRef" class="chart" />
        </div>
      </div>
    </div>

    <div class="screen-foot">
      <span>数据来源：本地业务库实时聚合</span>
      <span>生成时间：{{ generatedAt }}</span>
      <span>刷新间隔：{{ refreshSeconds }}s</span>
      <span v-if="error" style="color:#ff7875">{{ error }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { rptApi } from '@/api/modules'

const clock = ref('')
const widgets = ref([])
const screenName = ref('总览')
const refreshSeconds = ref(60)
const generatedAt = ref('-')
const error = ref('')
const pieRef = ref()
const barRef = ref()
const moneyRef = ref()

let charts = {}
let timer = null
let clockTimer = null

const UNITS = { OCCUPANCY_RATE: '%', BILL_UNPAID_AMOUNT: '元', PAYMENT_TOTAL_AMOUNT: '元' }

const kpis = computed(() => (widgets.value || []).slice(0, 4).map((w) => ({
  code: w.code,
  title: w.title,
  value: fmt(w.value),
  unit: UNITS[w.code] || '',
  tone: w.code === 'ACCESS_ABNORMAL_COUNT' && Number(w.value) > 0 ? 'danger'
    : (w.code === 'BILL_UNPAID_COUNT' && Number(w.value) > 0 ? 'warn'
      : (w.code === 'OCCUPANCY_RATE' ? 'ok' : ''))
})))

function fmt(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n.toLocaleString('zh-CN') : '-'
}

function valueOf(code) {
  const w = (widgets.value || []).find((x) => x.code === code)
  return w ? Number(w.value || 0) : 0
}

function initCharts() {
  charts.pie = echarts.init(pieRef.value)
  charts.bar = echarts.init(barRef.value)
  charts.money = echarts.init(moneyRef.value)
  window.addEventListener('resize', resize)
}

function resize() {
  Object.values(charts).forEach((c) => c && c.resize())
}

const AXIS = {
  axisLine: { lineStyle: { color: 'rgba(64,158,255,.35)' } },
  axisLabel: { color: '#8fb8e8', fontSize: 11 },
  splitLine: { lineStyle: { color: 'rgba(64,158,255,.12)' } }
}

function renderCharts() {
  const occupied = valueOf('HOUSE_OCCUPIED')
  const vacant = valueOf('HOUSE_VACANT')
  const total = valueOf('HOUSE_TOTAL')
  const other = Math.max(0, total - occupied - vacant)

  charts.pie?.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#8fb8e8', fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['48%', '70%'], center: ['50%', '44%'],
      label: { color: '#d6e4ff', fontSize: 11, formatter: '{b}\\n{c}' },
      data: [
        { name: '已出租', value: occupied, itemStyle: { color: '#3f8cff' } },
        { name: '空置', value: vacant, itemStyle: { color: '#ffc53d' } },
        { name: '其他', value: other, itemStyle: { color: '#4e5969' } }
      ]
    }]
  })

  charts.bar?.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 42, right: 14, top: 18, bottom: 26 },
    xAxis: { type: 'category', data: ['今日开门', '今日异常', '不可信占比%'], ...AXIS },
    yAxis: { type: 'value', ...AXIS },
    series: [{
      type: 'bar', barWidth: 26,
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#6db3ff' }, { offset: 1, color: '#1f4d8f' }
        ])
      },
      data: [valueOf('ACCESS_TODAY_COUNT'), valueOf('ACCESS_ABNORMAL_COUNT'), 0]
    }]
  })

  charts.money?.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 56, right: 16, top: 18, bottom: 26 },
    xAxis: { type: 'category', data: ['欠费金额', '累计收款'], ...AXIS },
    yAxis: { type: 'value', ...AXIS },
    series: [{
      type: 'line', smooth: true, symbolSize: 9,
      lineStyle: { width: 3, color: '#73d13d' },
      itemStyle: { color: '#73d13d' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(115,209,61,.45)' },
          { offset: 1, color: 'rgba(115,209,61,0)' }
        ])
      },
      data: [valueOf('BILL_UNPAID_AMOUNT'), valueOf('PAYMENT_TOTAL_AMOUNT')]
    }]
  })
}

async function load() {
  error.value = ''
  try {
    const data = await rptApi.screenData('OVERVIEW')
    screenName.value = data.screenName || '总览'
    refreshSeconds.value = data.refreshSeconds || 60
    generatedAt.value = data.generatedAt || '-'
    widgets.value = data.widgets || []
    await nextTick()
    if (!charts.pie) initCharts()
    renderCharts()
  } catch (e) {
    error.value = '数据加载失败（需登录且后端可达）'
  }
}

function tickClock() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  clock.value = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ` +
    `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

onMounted(async () => {
  tickClock()
  clockTimer = setInterval(tickClock, 1000)
  await load()
  timer = setInterval(load, Math.max(15, refreshSeconds.value) * 1000)
})

onUnmounted(() => {
  clearInterval(timer)
  clearInterval(clockTimer)
  window.removeEventListener('resize', resize)
  Object.values(charts).forEach((c) => c && c.dispose())
})
</script>
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个文件（大屏）' % count)
