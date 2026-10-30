<template>
  <div class="bp-page">
    <!-- 顶部两个筛选（对应参考系统的「演示/全部」） -->
    <div class="bp-page-head">
      <div>
        <h2>运营驾驶舱</h2>
        <div class="desc">
          数据实时聚合 · 刷新 {{ screen?.refreshSeconds || 60 }}s ·
          {{ metrics.generatedAt ? '更新于 ' + fmtTime(metrics.generatedAt) : '加载中' }}
        </div>
      </div>
      <div class="actions">
        <el-radio-group v-model="scope" size="small" @change="load">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="org">本组织</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :loading="loading" @click="load">
          <el-icon><Refresh /></el-icon>刷新
        </el-button>
        <el-button @click="openScreen">大屏</el-button>
      </div>
    </div>

    <!-- 第一行：房源结构（图表）+ 房源概况 + 合同 -->
    <div class="grid g4">
      <div class="stat-card">
        <div class="head">
          <span class="ico blue"><el-icon><PieChart /></el-icon></span>
          <el-tooltip content="按房源状态拆分：已出租 / 空置可租 / 待配租 / 其他，总数=房源台账条数" placement="top"><span class="t" style="cursor:help">房源结构 <span class="muted">ⓘ</span></span></el-tooltip>
          <span class="total">{{ n('HOUSE_TOTAL') }}</span>
        </div>
        <div ref="chartRef" class="chart" />
        <div class="pie-legend">
          <span v-for="x in pieItems" :key="x.name" class="pie-legend-item">
            <i :style="{ background: x.color }" />
            <em>{{ x.name }}</em>
            <b>{{ Number(x.value).toLocaleString() }}</b>
          </span>
        </div>
      </div>

      <div class="stat-card">
        <div class="head">
          <span class="ico green"><el-icon><OfficeBuilding /></el-icon></span>
          <el-tooltip content="已出租=状态 OCCUPIED；空置可租=VACANT；出租率=已出租÷房源总数" placement="top"><span class="t" style="cursor:help">房源概况 <span class="muted">ⓘ</span></span></el-tooltip>
          <span class="total">{{ n('HOUSE_TOTAL') }}</span>
        </div>
        <div class="rows">
          <div class="row"><span>已出租</span><b class="ok">{{ n('HOUSE_OCCUPIED') }}</b></div>
          <div class="row"><span>空置可租</span><b class="warn">{{ n('HOUSE_VACANT') }}</b></div>
          <div class="row"><span>出租率</span><b class="ok">{{ rate }}%</b></div>
          <div class="row"><span>待配租</span><b>{{ n('PENDING_ALLOC') }}</b></div>
        </div>
      </div>

      <div class="stat-card">
        <div class="head">
          <span class="ico orange"><el-icon><Money /></el-icon></span>
          <el-tooltip content="欠费金额=应收−已缴的正数部分；收缴率=累计收款÷累计应收" placement="top"><span class="t" style="cursor:help">财务应收 <span class="muted">ⓘ</span></span></el-tooltip>
          <span class="total">{{ money('BILL_UNPAID_AMOUNT') }}</span>
        </div>
        <div class="rows">
          <div class="row"><span>欠费账单</span><b class="danger">{{ n('BILL_UNPAID_COUNT') }}</b></div>
          <div class="row"><span>累计收款</span><b class="ok">{{ money('PAYMENT_TOTAL_AMOUNT') }}</b></div>
          <div class="row"><span>收缴率</span><b :class="collectRate >= 90 ? 'ok' : 'warn'">
            {{ collectRate }}%</b></div>
          <div class="row"><span>补贴发放</span><b>{{ subsidyCount }} 笔</b></div>
        </div>
      </div>

      <div class="stat-card">
        <div class="head">
          <span class="ico red"><el-icon><Warning /></el-icon></span>
          <span class="t">设备风控</span>
          <span class="total">{{ n('ACCESS_ABNORMAL_COUNT') }}</span>
        </div>
        <div class="rows">
          <div class="row"><span>今日开门</span><b>{{ n('ACCESS_TODAY_COUNT') }}</b></div>
          <div class="row"><span>异常开门</span>
            <b :class="n('ACCESS_ABNORMAL_COUNT') > 0 ? 'danger' : 'ok'">
              {{ n('ACCESS_ABNORMAL_COUNT') }}</b></div>
          <div class="row"><span>告警待处理</span><b class="warn">{{ alertPending }}</b></div>
          <div class="row"><span>工单待办</span><b>{{ workOrderPending }}</b></div>
        </div>
      </div>
    </div>

    <!-- 第二行：待办类（对应参考系统的 租客合同/投诉/预定/线索待办） -->
    <div class="grid g3">
      <div class="stat-card">
        <div class="head">
          <span class="ico blue"><el-icon><Tickets /></el-icon></span>
          <el-tooltip content="待受理=已提交未受理；审核中=受理后未终审；已通过=终审通过" placement="top"><span class="t" style="cursor:help">申请与审批 <span class="muted">ⓘ</span></span></el-tooltip>
          <span class="total">{{ appTotal }}</span>
        </div>
        <div class="rows">
          <div v-for="x in appStats" :key="x.label" class="row">
            <span>{{ x.label }}</span>
            <b :class="x.tone || ''">{{ x.value }}</b>
          </div>
          <div v-if="!appStats.length" class="row empty">暂无数据</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="head">
          <span class="ico orange"><el-icon><Wallet /></el-icon></span>
          <el-tooltip content="押金按收取/退还/待退三态统计，金额单位元" placement="top"><span class="t" style="cursor:help">押金与退款 <span class="muted">ⓘ</span></span></el-tooltip>
          <span class="total">{{ depositTotal }}</span>
        </div>
        <div class="rows">
          <div v-for="x in depositStats" :key="x.label" class="row">
            <span>{{ x.label }}</span>
            <b :class="x.tone || ''">{{ x.value }}</b>
          </div>
          <div v-if="!depositStats.length" class="row empty">暂无数据</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="head">
          <span class="ico green"><el-icon><Bell /></el-icon></span>
          <el-tooltip content="工单与告警按待处理/处理中/已处理统计，含今日新增" placement="top"><span class="t" style="cursor:help">服务与待办 <span class="muted">ⓘ</span></span></el-tooltip>
          <span class="total">{{ serviceTotal }}</span>
        </div>
        <div class="rows">
          <div v-for="x in serviceStats" :key="x.label" class="row">
            <span>{{ x.label }}</span>
            <b :class="x.tone || ''">{{ x.value }}</b>
          </div>
          <div v-if="!serviceStats.length" class="row empty">暂无数据</div>
        </div>
      </div>
    </div>

    <!-- 经营趋势 -->
    <el-row :gutter="12" style="margin-bottom:14px">
      <el-col :span="12">
        <div class="bp-card">
          <div class="head">应收 / 实收趋势（近 6 月）</div>
          <LineTrend :rows="billTrend" color="#1890ff" :height="190" />
        </div>
      </el-col>
      <el-col :span="12">
        <div class="bp-card">
          <div class="head">能耗用量趋势（近 6 月）</div>
          <LineTrend :rows="energyTrend" color="#faad14" :height="190" />
        </div>
      </el-col>
    </el-row>

    <!-- 指标明细 -->
    <div class="bp-card">
      <div class="head">指标明细</div>
      <el-table :data="metricRows" size="small" border>
        <el-table-column prop="label" label="指标名称" width="180" />
        <el-table-column prop="code" label="编码" width="240" />
        <el-table-column prop="value" label="当前值" align="right" width="160" />
        <el-table-column prop="hint" label="说明" min-width="220" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import req from '@/api/request'
import { rptApi } from '@/api/modules'
import { metricLabel, metricUnit } from '@/constants/metrics'
import LineTrend from '@/components/LineTrend.vue'

const HINTS = {
  HOUSE_TOTAL: '组织范围内全部房源',
  HOUSE_OCCUPIED: '已出租（含已配租）',
  HOUSE_VACANT: '可配租的空置房源',
  OCCUPANCY_RATE: '已出租 / 房源总数',
  BILL_UNPAID_AMOUNT: '未核销的应收金额',
  BILL_UNPAID_COUNT: '未缴清的账单数',
  PAYMENT_TOTAL_AMOUNT: '累计登记收款',
  ACCESS_TODAY_COUNT: '当日门禁开门次数',
  ACCESS_ABNORMAL_COUNT: '重复/尾随/超时等异常'
}

const loading = ref(false)
const screen = ref(null)
const metrics = ref({})
const scope = ref('all')
const chartRef = ref()
const billTrendRows = ref([])
const energyTrendRows = ref([])
const billTrend = computed(() => billTrendRows.value.map((x) => ({
  label: String(x.month || '').slice(5), value: Number(x.receivable) || 0
})))
const energyTrend = computed(() => energyTrendRows.value.map((x) => ({
  label: String(x.month || '').slice(5), value: Number(x.usage) || 0
})))
let chart = null

/** 指标表为空时的房源状态兜底统计（否则饼图无数据、看起来像「没有文字」） */
const houseStat = ref({ occupied: 0, vacant: 0, pending: 0 })

/** 房源结构饼图数据（图例与图表共用） */
const pieItems = computed(() => {
  const occupied = Number(metrics.value.HOUSE_OCCUPIED || houseStat.value.occupied || 0)
  const vacant = Number(metrics.value.HOUSE_VACANT || houseStat.value.vacant || 0)
  const pending = Number(metrics.value.PENDING_ALLOC || houseStat.value.pending || 0)
  return [
    { name: '已出租', value: occupied, color: '#1890ff' },
    { name: '空置', value: vacant, color: '#faad14' },
    { name: '待配租', value: pending, color: '#722ed1' }
  ]
})

/** 按图表容器（逐级向上）的实际背景挑选可读的文字颜色 */
function contrastText() {
  try {
    let el = chartRef.value
    let lum = 255          // 默认视为浅色底
    while (el) {
      const bg = getComputedStyle(el).backgroundColor || ''
      // rgba(...) 最后一维是 alpha：透明背景（alpha=0）不能当作黑色
      const m = bg.match(/rgba?\(([^)]+)\)/)
      if (m) {
        const parts = m[1].split(/[,\s/]+/).map(Number)
        const alpha = parts.length > 3 ? parts[3] : 1
        if (alpha > 0.1) {
          lum = 0.299 * parts[0] + 0.587 * parts[1] + 0.114 * parts[2]
          break
        }
      }
      el = el.parentElement
    }
    return lum < 128 ? 'rgba(255,255,255,0.9)' : 'rgba(0,0,0,0.72)'
  } catch (e) {
    return 'rgba(0,0,0,0.72)'
  }
}
async function loadHouseFallback() {
  const one = async (status) => {
    try {
      const d = await req.get('/houses', { params: { pageNum: 1, pageSize: 1, houseStatus: status } })
      return Number(d.total || 0)
    } catch (e) { return 0 }
  }
  const [o, v, p] = await Promise.all([one('OCCUPIED'), one('VACANT'), one('PENDING_ALLOC')])
  houseStat.value = { occupied: o, vacant: v, pending: p }
}

// 各统计卡数据
const appStats = ref([])
const appTotal = ref(0)
const depositStats = ref([])
const depositTotal = ref(0)
const serviceStats = ref([])
const serviceTotal = ref(0)
const alertPending = ref(0)
const workOrderPending = ref(0)
const subsidyCount = ref(0)

function n(code) {
  const v = Number(metrics.value[code] || 0)
  return v.toLocaleString('zh-CN')
}
function money(code) {
  const v = Number(metrics.value[code] || 0)
  return '¥' + v.toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}
function fmtTime(t) {
  return String(t).replace('T', ' ').slice(0, 19)
}

const rate = computed(() => Number(metrics.value.OCCUPANCY_RATE || 0).toFixed(2))
const collectRate = computed(() => {
  const unpaid = Number(metrics.value.BILL_UNPAID_AMOUNT || 0)
  const paid = Number(metrics.value.PAYMENT_TOTAL_AMOUNT || 0)
  const total = unpaid + paid
  return total > 0 ? (paid / total * 100).toFixed(1) : '0.0'
})

const metricRows = computed(() =>
  Object.entries(metrics.value)
    .filter(([k]) => k !== 'generatedAt')
    .map(([code, value]) => ({
      code, label: metricLabel(code),
      value: Number(value).toLocaleString('zh-CN') + (metricUnit(code) || ''),
      hint: HINTS[code] || '-'
    }))
)

/** 经营趋势数据：账单应收/实收 + 能耗用量 */
async function loadTrendCharts() {
  try {
    const bills = await req.get('/fin/bills/trend', { params: { months: 6 } })
    billTrendRows.value = bills || []
  } catch (e) { billTrendRows.value = [] }
  // 首次进入时偶发失败（并发请求过多），重试一次再放弃
  for (let i = 0; i < 2; i++) {
    try {
      const en = await req.get('/fin/meter-readings/analytics', { params: { months: 6 } })
      energyTrendRows.value = (en && en.months) || []
      break
    } catch (e) {
      energyTrendRows.value = []
      await new Promise((r) => setTimeout(r, 800))
    }
  }
}

function renderChart() {
  if (!chart) return
  // 指标优先，为空时用实时统计兜底
  // 文字颜色跟随容器背景亮度：深色卡片用浅色字，浅色卡片用深色字
  const textColor = contrastText()
  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}：{c} 套（{d}%）'
    },
    // 图例由卡片底部的 HTML 渲染，避免与饼图标签重叠
    legend: { show: false },
    color: ['#1890ff', '#faad14', '#722ed1'],
    series: [{
      type: 'pie',
      radius: ['42%', '62%'],
      center: ['50%', '46%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: 'transparent', borderWidth: 2 },
      label: {
        show: true,
        formatter: '{d}%',
        color: textColor,
        fontSize: 11,
        lineHeight: 14,
        overflow: 'none'
      },
      labelLine: { show: true, length: 8, length2: 10, lineStyle: { color: '#9aa4b2' } },
      data: pieItems.value.map((x) => ({
        name: x.name, value: x.value, itemStyle: { color: x.color }
      }))
    }]
  }, true)
}

/** 按状态分组统计某个列表接口 */
async function statByStatus(path, field, mapping) {
  try {
    const d = await req.get(path, { params: { pageNum: 1, pageSize: 500 } })
    const rows = d.rows || d || []
    const group = {}
    rows.forEach((r) => {
      const k = r[field] || 'UNKNOWN'
      group[k] = (group[k] || 0) + 1
    })
    const stats = mapping
      .filter((m) => group[m.code])
      .map((m) => ({
        label: m.label,
        value: group[m.code],
        tone: m.tone ? m.tone(group[m.code]) : ''
      }))
    return { stats, total: rows.length, group }
  } catch (e) {
    return { stats: [], total: 0, group: {} }
  }
}

async function loadCards() {
  // 申请与审批
  const a = await statByStatus('/applications', 'applicationStatus', [
    { code: 'SUBMITTED', label: '待受理', tone: () => 'warn' },
    { code: 'ACCEPTED', label: '已受理' },
    { code: 'REVIEWING', label: '审核中', tone: () => 'warn' },
    { code: 'APPROVED', label: '已通过', tone: () => 'ok' },
    { code: 'REJECTED', label: '已驳回', tone: () => 'danger' }
  ])
  appStats.value = a.stats
  appTotal.value = a.total

  // 押金与退款
  const dep = await statByField('/fin/deposits', 'depositStatus', [
    { code: 'HELD', label: '已收讫' },
    { code: 'DEDUCTED', label: '已抵扣', tone: () => 'warn' },
    { code: 'REFUNDED', label: '已退还', tone: () => 'ok' }
  ])
  const ref = await statByField('/fin/refunds', 'refundStatus', [
    { code: 'PENDING', label: '退款待审', tone: () => 'warn' },
    { code: 'APPROVED', label: '已批准' },
    { code: 'SUCCESS', label: '已打款', tone: () => 'ok' }
  ])
  depositStats.value = [...dep.stats, ...ref.stats]
  depositTotal.value = dep.total + ref.total

  // 服务与待办
  const wo = await statByField('/workorders', 'orderStatus', [
    { code: 'PENDING', label: '工单待派', tone: () => 'warn' },
    { code: 'PROCESSING', label: '处理中' },
    { code: 'FINISHED', label: '已完成', tone: () => 'ok' }
  ])
  const al = await statByField('/alerts', 'alertStatus', [
    { code: 'PENDING', label: '告警待处理', tone: (v) => (v > 0 ? 'danger' : '') },
    { code: 'HANDLED', label: '告警已处理' }
  ])
  const cp = await statByField('/complaints', 'complaintStatus', [
    { code: 'PENDING', label: '投诉待办', tone: () => 'warn' },
    { code: 'CLOSED', label: '投诉办结', tone: () => 'ok' }
  ])
  serviceStats.value = [...wo.stats, ...al.stats, ...cp.stats]
  serviceTotal.value = wo.total + al.total + cp.total
  workOrderPending.value = wo.group.PENDING || 0
  alertPending.value = al.group.PENDING || 0

  // 补贴笔数
  try {
    const sub = await req.get('/fin/subsidies/records',
      { params: { pageNum: 1, pageSize: 1 } })
    subsidyCount.value = Number(sub.total || 0)
  } catch (e) { /* ignore */ }
}

async function statByField(path, field, mapping) {
  return statByStatus(path, field, mapping)
}

async function load() {
  loading.value = true
  try {
    const data = await rptApi.screenData('OVERVIEW')
    screen.value = data
    metrics.value = await rptApi.metrics()
    // 指标表为空时（未跑聚合任务），饼图会没有任何扇区，看起来像「没有文字」。
    // 这里按房源状态实时兜底统计，保证图表始终有数据。
    await loadHouseFallback()
    await nextTick()
    if (!chart) {
      chart = echarts.init(chartRef.value)
      window.addEventListener('resize', onResize)
    }
    renderChart()
    // 容器在 flex 布局中可能刚拿到高度，补一次 resize 避免圆环只画一角
    setTimeout(() => chart && chart.resize(), 120)
    await loadCards()
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

function onResize() { chart && chart.resize() }
function openScreen() {
  window.open('./view-screen.html', 'bp-screen', 'width=1600,height=900')
}

onMounted(async () => { await load(); nextTick(() => loadTrendCharts()) })
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart && chart.dispose()
})
</script>

<style scoped>
.grid { display: grid; gap: 12px; margin-bottom: 16px; }
.g4 { grid-template-columns: repeat(4, 1fr); }
.g3 { grid-template-columns: repeat(3, 1fr); }
@media (max-width: 1400px) { .g4 { grid-template-columns: repeat(2, 1fr); } }

/* 统计卡：与参考系统一致的「标题 + 合计 + 分项行」 */
.stat-card {
  background: var(--bp-card-bg, #fff);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 14px 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  min-height: 176px;
  display: flex;
  flex-direction: column;
}
.stat-card .head {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 10px;
}
.stat-card .ico {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 13px; flex: 0 0 24px;
}
.ico.blue { background: #1890ff; }
.ico.green { background: #52c41a; }
.ico.orange { background: #fa8c16; }
.ico.red { background: #ff4d4f; }
.stat-card .t { font-size: 14px; color: var(--el-text-color-primary); }
.stat-card .total {
  margin-left: auto;
  font-size: 20px; font-weight: 500;
  color: var(--el-text-color-primary);
  font-variant-numeric: tabular-nums;
}
.stat-card .rows { flex: 1; }
.stat-card .row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 7px 0;
  font-size: 13px;
  color: var(--el-text-color-regular);
  border-bottom: 1px dashed #f5f5f5;
}
.stat-card .row:last-child { border-bottom: none; }
.stat-card .row b {
  font-size: 16px; font-weight: 500;
  color: var(--el-text-color-primary);
  font-variant-numeric: tabular-nums;
}
.stat-card .row b.ok { color: #52c41a; }
.stat-card .row b.warn { color: #faad14; }
.stat-card .row b.danger { color: #ff4d4f; }
.stat-card .row.empty { color: var(--el-text-color-secondary); justify-content: center; }
.chart { flex: 1; min-height: 118px; }
.pie-legend {
  display: flex; justify-content: center; flex-wrap: wrap;
  gap: 3px 8px; padding: 4px 0 2px;
  font-size: 10.5px; color: var(--el-text-color-regular);
}
.pie-legend-item { display: inline-flex; align-items: center; gap: 3px; }
.pie-legend-item i {
  width: 8px; height: 8px; border-radius: 2px; display: inline-block;
}
.pie-legend-item em { font-style: normal; }
.pie-legend-item b { color: var(--el-text-color-primary); font-weight: 600; }
:global(html.dark) .pie-legend { color: rgba(255, 255, 255, 0.75); }
:global(html.dark) .pie-legend-item b { color: #fff; }
</style>
