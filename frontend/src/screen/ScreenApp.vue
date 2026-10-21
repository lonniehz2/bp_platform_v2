<template>
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
import { metricLabel, metricUnit } from '@/constants/metrics'

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
let chartsRo = null
let timer = null
let clockTimer = null



const kpis = computed(() => (widgets.value || []).slice(0, 4).map((w) => ({
  code: w.code,
  title: (!w.title || w.title === w.code) ? metricLabel(w.code) : w.title,
  value: fmt(w.value),
  unit: metricUnit(w.code),
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
  if (charts.pie) return
  charts.pie = echarts.init(pieRef.value || undefined)
  charts.bar = echarts.init(barRef.value || undefined)
  charts.money = echarts.init(moneyRef.value || undefined)
  window.addEventListener('resize', resize)
  // 某些浏览器首帧容器高度为 0，下一帧再校正一次
  requestAnimationFrame(() => resize())
}

function resize() {
  Object.values(charts).forEach((c) => {
    // 只对真正的 echarts 实例调用，避免 ResizeObserver 等混入导致报错
    if (c && typeof c.resize === "function") c.resize()
  })
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
      label: { color: '#d6e4ff', fontSize: 11, formatter: '{b}\n{c}' },
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
    error.value = '数据加载失败：请确认已登录且后端可达后点「刷新」'
    // 仍渲染图表框架，避免整屏空白
    if (charts.pie) renderCharts()
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
  // 先建图（此时容器已有尺寸），再取数据；避免取数失败导致空白
  await nextTick()
  initCharts()
  renderCharts()
  // 容器尺寸变化（侧边栏折叠/缩放）时确保图表跟随
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => resize())
    ;[pieRef.value, barRef.value, moneyRef.value].forEach((el) => el && ro.observe(el))
    chartsRo = ro
  }
  await load()
  timer = setInterval(load, Math.max(15, refreshSeconds.value) * 1000)
})

onUnmounted(() => {
  clearInterval(timer)
  clearInterval(clockTimer)
  window.removeEventListener('resize', resize)
  Object.values(charts).forEach((c) => c && typeof c.dispose === "function" && c.dispose())
})
</script>
