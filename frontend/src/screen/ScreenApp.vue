<template>
  <div class="screen-wrap">
    <div class="screen-head">
      <h1>{{ t('screen.title') }}</h1>
      <el-tag size="small" style="background:transparent;color:#6db3ff;border-color:#2a5b96">
        {{ screenName }}
      </el-tag>
      <div class="spacer" />
      <span class="clock">{{ clock }}</span>
      <el-button size="small" type="primary" plain @click="load">{{ t('screen.refresh') }}</el-button>
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
          <div class="title">{{ t('screen.housingMix') }}</div>
          <div ref="pieRef" class="chart" />
        </div>
        <div class="panel">
          <div class="title">{{ t('screen.accessTrend') }}</div>
          <div ref="barRef" class="chart" />
        </div>
        <div class="panel">
          <div class="title">{{ t('screen.money') }}</div>
          <div ref="moneyRef" class="chart" />
        </div>
      </div>
      <!-- 值班关注：挂墙时最要紧的是「有多少事等着处理」 -->
      <div class="kpi-row focus-row">
        <div v-for="f in focusList" :key="f.label" class="kpi" :class="f.tone">
          <div class="label">{{ f.label }}</div>
          <div class="value">
            {{ f.value }}<span class="unit">{{ f.unit }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="screen-foot">
        <span>{{ t('screen.source') }}</span>
      <span>{{ t('screen.generated', { time: generatedAt }) }}</span>
      <span>{{ t('screen.interval', { s: refreshSeconds }) }}</span>
      <span v-if="error" style="color:#ff7875">{{ error }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { rptApi } from '@/api/modules'
import req from '@/api/request'
import { metricLabel, metricUnit } from '@/constants/metrics'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const clock = ref('')
const widgets = ref([])
const screenName = ref(t('screen.overview'))
const refreshSeconds = ref(60)
const generatedAt = ref('-')
const error = ref('')
const pieRef = ref()
const barRef = ref()
const moneyRef = ref()

/**
 * 值班关注：挂墙场景最关心「有多少事等着处理」。
 * 数据直接取业务列表的 total，避免依赖指标聚合任务是否跑过。
 */
const focus = ref({ todo: 0, unpaid: 0, effective: 0, renewing: 0 })
/** 大屏 widgets 缺房源分类时的兜底统计 */
const houseStat = ref({ occupied: 0, vacant: 0, pending: 0 })
const focusList = computed(() => [
  { label: t('screen.todo'), value: focus.value.todo, unit: t('screen.unitItem'), tone: focus.value.todo > 20 ? 'warn' : '' },
  { label: t('screen.unpaid'), value: focus.value.unpaid, unit: t('screen.unitBill'), tone: focus.value.unpaid > 0 ? 'warn' : '' },
  { label: t('screen.effective'), value: focus.value.effective, unit: t('screen.unitContract'), tone: 'ok' },
  { label: t('screen.renewing'), value: focus.value.renewing, unit: t('screen.unitContract'), tone: '' }
])

async function loadFocus() {
  const total = async (path, params) => {
    try {
      const d = await req.get(path, { params: { pageNum: 1, pageSize: 1, ...params } })
      return Number(d.total || 0)
    } catch (e) { return 0 }
  }
  const [todo, unpaid, effective, renewing, occ, vac, pend] = await Promise.all([
    total('/messages/todos', { status: 'PENDING' }),
    total('/fin/bills', { status: 'UNPAID' }),
    // 注意：/contracts 的筛选参数名是 status（不是 contractStatus），传错会被忽略
    total('/contracts', { status: 'EFFECTIVE' }),
    total('/contracts', { status: 'RENEWING' }),
    total('/houses', { houseStatus: 'OCCUPIED' }),
    total('/houses', { houseStatus: 'VACANT' }),
    total('/houses', { houseStatus: 'PENDING_ALLOC' })
  ])
  focus.value = { todo, unpaid, effective, renewing }
  // 大屏 widgets 里不含 HOUSE_OCCUPIED / PENDING_ALLOC，缺失时用实时统计兜底，
  // 否则饼图会变成「已出租 0% / 其他 61%」这种误导性结果
  houseStat.value = { occupied: occ, vacant: vac, pending: pend }
}

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
  // widget 优先，缺失时用实时统计兜底（大屏 widgets 不含已出租/待配租）
  const occupied = valueOf('HOUSE_OCCUPIED') || houseStat.value.occupied
  const vacant = valueOf('HOUSE_VACANT') || houseStat.value.vacant
  const total = valueOf('HOUSE_TOTAL')
  // 与「运营驾驶舱」口径统一：第三类用「待配租」，不再是笼统的「其他」
  const pending = valueOf('PENDING_ALLOC') || houseStat.value.pending
  const other = Math.max(0, total - occupied - vacant - pending)

  charts.pie?.setOption({
    tooltip: { trigger: 'item', formatter: '{b}：{c} 套（{d}%）' },
    // 深色大屏：三个色块排在圆饼下方一行，字号与间距收紧避免换行
    legend: {
      bottom: 0,
      left: 'center',
      orient: 'horizontal',
      itemGap: 12,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#cfe2ff', fontSize: 11 },
    },
    series: [{
      type: 'pie', radius: ['44%', '66%'], center: ['50%', '40%'],
      label: { color: '#eaf2ff', fontSize: 11, formatter: '{b}\n{d}%', lineHeight: 15 },
      labelLine: { show: true, length: 8, length2: 10, lineStyle: { color: '#8fb8e8' } },
      data: [
        { name: '已出租', value: occupied, itemStyle: { color: '#3f8cff' } },
        { name: '空置', value: vacant, itemStyle: { color: '#ffc53d' } },
        { name: '待配租', value: pending, itemStyle: { color: '#8b5cf6' } },
        // 只有确实存在「以上三类之外」的房源时才显示，避免与驾驶舱口径不一致
        ...(other > 0 ? [{ name: '其他', value: other, itemStyle: { color: '#64748b' } }] : [])
      ]
    }]
  })

  charts.bar?.setOption({
    tooltip: { trigger: 'axis' },
    // 左侧留 64px 并压缩数字（12万），否则 6 位数刻度会被裁掉首位
    grid: { left: 64, right: 14, top: 18, bottom: 26 },
    xAxis: { type: 'category', data: ['今日开门', '今日异常', '不可信占比%'], ...AXIS },
    yAxis: {
      type: 'value',
      ...AXIS,
      axisLabel: {
        ...AXIS.axisLabel,
        formatter: (v) => (v >= 10000 ? Math.round(v / 1000) / 10 + '万' : v)
      }
    },
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
    await loadFocus()
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
