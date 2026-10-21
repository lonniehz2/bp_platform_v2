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
          <span class="t">房源结构</span>
          <span class="total">{{ n('HOUSE_TOTAL') }}</span>
        </div>
        <div ref="chartRef" class="chart" />
      </div>

      <div class="stat-card">
        <div class="head">
          <span class="ico green"><el-icon><OfficeBuilding /></el-icon></span>
          <span class="t">房源概况</span>
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
          <span class="t">财务应收</span>
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
          <span class="t">申请与审批</span>
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
          <span class="t">押金与退款</span>
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
          <span class="t">服务与待办</span>
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
let chart = null

/** 指标表为空时的房源状态兜底统计（否则饼图无数据、看起来像「没有文字」） */
const houseStat = ref({ occupied: 0, vacant: 0, pending: 0 })

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

function renderChart() {
  if (!chart) return
  // 指标优先，为空时用实时统计兜底
  const occupied = Number(metrics.value.HOUSE_OCCUPIED || houseStat.value.occupied || 0)
  const vacant = Number(metrics.value.HOUSE_VACANT || houseStat.value.vacant || 0)
  const pending = Number(metrics.value.PENDING_ALLOC || houseStat.value.pending || 0)
  // 文字颜色跟随容器背景亮度：深色卡片用浅色字，浅色卡片用深色字，
  // 否则深色风格下标签几乎看不见（此前硬编码 rgba(0,0,0,0.75)）
  const textColor = contrastText()
  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}：{c} 套（{d}%）'
    },
    legend: {
      bottom: 0,
      left: 'center',
      orient: 'horizontal',
      // 三个色块强制排成一行：缩小字号与间距，且图例不带数量（数量在 tooltip 里）
      itemGap: 10,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: textColor, fontSize: 11 }
    },
    color: ['#1890ff', '#faad14', '#722ed1'],
    series: [{
      type: 'pie',
      radius: ['46%', '68%'],
      center: ['50%', '42%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: 'transparent', borderWidth: 2 },
      label: {
        show: true,
        // 名称 + 百分比，两行显示，保证阅读时能对上颜色
        formatter: '{b}\n{d}%',
        color: textColor,
        fontSize: 12,
        lineHeight: 16
      },
      labelLine: { show: true, length: 10, length2: 12, lineStyle: { color: textColor } },
      data: [
        { name: '已出租', value: occupied, itemStyle: { color: '#1890ff' } },
        { name: '空置', value: vacant, itemStyle: { color: '#faad14' } },
        // 原 #52c41a（绿）与空置橙在视觉上偏近，改为紫色拉开色相差
        { name: '待配租', value: pending, itemStyle: { color: '#722ed1' } }
      ]
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

onMounted(load)
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
  background: #fff;
  border: 1px solid #f0f0f0;
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
.stat-card .t { font-size: 14px; color: rgba(0, 0, 0, 0.85); }
.stat-card .total {
  margin-left: auto;
  font-size: 20px; font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  font-variant-numeric: tabular-nums;
}
.stat-card .rows { flex: 1; }
.stat-card .row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 7px 0;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);
  border-bottom: 1px dashed #f5f5f5;
}
.stat-card .row:last-child { border-bottom: none; }
.stat-card .row b {
  font-size: 16px; font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  font-variant-numeric: tabular-nums;
}
.stat-card .row b.ok { color: #52c41a; }
.stat-card .row b.warn { color: #faad14; }
.stat-card .row b.danger { color: #ff4d4f; }
.stat-card .row.empty { color: rgba(0, 0, 0, 0.25); justify-content: center; }
.chart { flex: 1; min-height: 150px; }
</style>
