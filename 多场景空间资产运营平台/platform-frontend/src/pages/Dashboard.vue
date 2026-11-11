<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { api } from '../api'
import { mode } from '../ui'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const projects = ref([])
const project = ref(null)
const applications = ref([])
const contracts = ref([])
const bills = ref([])
const devices = ref([])
const houses = ref([])
const payments = ref([])
const alerts = ref([])
const workOrders = ref([])
const periodMode = ref('month')
const customStart = ref('')
const customEnd = ref('')
const summary = ref(null)
const compare = ref([])
const houseChart = ref(null)
const trendChart = ref(null)
const statusChart = ref(null)
const deviceChart = ref(null)
let charts = []

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
const count = (list, status, field) => list.filter(x => x[field] === status).length
const rate = (a, b) => b ? Math.round(a / b * 1000) / 10 : 0
const orgSummary = computed(() => {
  const rows = compare.value || []
  const houses = rows.reduce((n, p) => n + Number(p.houses || 0), 0)
  const rented = rows.reduce((n, p) => n + Number(p.rentedHouses || 0), 0)
  const receivable = rows.reduce((n, p) => n + Number(p.receivable || 0), 0)
  const received = rows.reduce((n, p) => n + Number(p.received || 0), 0)
  return { projects: rows.length, houses, rented, occupancy: rate(rented, houses), receivable, received, collection: rate(received, receivable), outstanding: rows.reduce((n, p) => n + Number(p.outstanding || 0), 0) }
})
const rankedCompare = computed(() => (compare.value || []).slice().sort((a, b) => Number(b.occupancyRate || 0) - Number(a.occupancyRate || 0)))
function focusProject(id) { localStorage.setItem('platformProjectId', String(id)); load() }

async function load() {
  loading.value = true; error.value = ''
  try {
    projects.value = await api.projects()
    compare.value = await api.reportCompare()
    const saved = String(localStorage.getItem('platformProjectId') || '')
    project.value = projects.value.find(p => String(p.id) === saved)
      || projects.value.slice().sort((a, b) => ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) - ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0)))[0]
      || null
    if (project.value) {
      const id = project.value.id
      const [a, c, b, d, h, p, al, w] = await Promise.all([
        api.applications(id), api.contracts(id), api.bills(id), api.devices(id),
        api.houses(id), api.payments(id), api.alerts(id), api.workOrders(id)
      ])
      applications.value = a; contracts.value = c; bills.value = b; devices.value = d
      houses.value = h; payments.value = p; alerts.value = al; workOrders.value = w
      summary.value = null
      await loadSummary()
    }
    await nextTick()
    renderCharts()
  } catch (e) { error.value = e.message } finally { loading.value = false }
}

const houseStats = () => {
  const occupied = houses.value.filter(h => h.houseStatus === 'ALLOCATED' || h.houseStatus === 'OCCUPIED').length
  const vacant = houses.value.filter(h => h.houseStatus === 'VACANT').length
  return { occupied, vacant, total: houses.value.length }
}
const pad = (n) => String(n).padStart(2, '0')
const dateText = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const periodRange = computed(() => {
  const now = new Date()
  let start = new Date(now.getFullYear(), now.getMonth(), 1)
  let end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  if (periodMode.value === 'quarter') {
    const q = Math.floor(now.getMonth() / 3) * 3
    start = new Date(now.getFullYear(), q, 1)
    end = new Date(now.getFullYear(), q + 3, 0)
  } else if (periodMode.value === 'year') {
    start = new Date(now.getFullYear(), 0, 1)
    end = new Date(now.getFullYear(), 11, 31)
  } else if (periodMode.value === 'custom' && customStart.value && customEnd.value) {
    start = new Date(customStart.value)
    end = new Date(customEnd.value)
  }
  return { start: dateText(start), end: dateText(end) }
})
const isOpening = (b) => b.sourceType === 'OPENING'
const billInRange = (b) => {
  const d = String(b.periodStart || '').slice(0, 10)
  return d >= periodRange.value.start && d <= periodRange.value.end
}
const currentBills = computed(() => bills.value.filter(b => !isOpening(b) && billInRange(b)))
const openingBills = computed(() => bills.value.filter(b => isOpening(b)))
const billStats = () => {
  if (summary.value) {
    return {
      total: Number(summary.value.currentReceivable || 0),
      paid: Number(summary.value.currentPaid || 0),
      outstanding: Number(summary.value.currentOutstanding || 0),
      opening: Number(summary.value.openingOutstanding || 0),
      openingRecovery: Number(summary.value.openingRecovery || 0),
      totalOutstanding: Number(summary.value.totalOutstanding || 0),
      rate: Number(summary.value.currentRate || 0)
    }
  }
  const total = currentBills.value.reduce((s, b) => s + Number(b.payableAmount || b.amount || 0), 0)
  const paid = currentBills.value.reduce((s, b) => s + Number(b.paidAmount || 0), 0)
  const outstanding = Math.max(0, total - paid)
  const opening = openingBills.value.reduce((s, b) => s + Math.max(0, Number(b.payableAmount || b.amount || 0) - Number(b.paidAmount || 0)), 0)
  const openingRecovery = openingBills.value.reduce((s, b) => s + Number(b.paidAmount || 0), 0)
  return { total, paid, outstanding, opening, openingRecovery, totalOutstanding: opening + outstanding, rate: rate(paid, total) }
}
const monthlyBills = () => {
  const map = new Map()
  for (const b of bills.value) {
    const key = String(b.periodStart || '').slice(0, 7)
    if (!key) continue
    const item = map.get(key) || { key, amount: 0, paid: 0 }
    item.amount += Number(b.payableAmount || b.amount || 0)
    item.paid += Number(b.paidAmount || 0)
    map.set(key, item)
  }
  return [...map.values()].sort((a, b) => a.key.localeCompare(b.key)).slice(-8)
}
const deviceStats = () => {
  const map = new Map()
  const labels = { LOCK: '门锁', METER: '水电表', WATER_METER: '水表', ELEC_METER: '电表', ELECTRICITY_METER: '电表', GAS_METER: '燃气表', ELEVATOR: '电梯', GATE: '门禁' }
  for (const d of devices.value) {
    const key = d.deviceType || 'OTHER'
    map.set(key, (map.get(key) || 0) + 1)
  }
  return [...map.entries()].map(([key, value]) => ({ name: labels[key] || key, value }))
}

function drillBilling() {
  if (!project.value) return
  localStorage.setItem('platformProjectId', project.value.id)
  router.push({ path: '/billing', query: {
    periodStart: periodRange.value.start,
    periodEnd: periodRange.value.end
  } })
}

function colors() {
  const dark = document.documentElement.classList.contains('dark')
  return {
    text: dark ? '#cbd5e1' : '#595959',
    line: dark ? '#334155' : '#e8e8e8',
    blue: '#1890ff', green: '#52c41a', orange: '#faad14', red: '#ff4d4f', purple: '#722ed1'
  }
}

function renderCharts() {
  charts.forEach(c => c.dispose())
  charts = []
  const c = colors()
  if (houseChart.value) {
    const s = houseStats()
    const chart = echarts.init(houseChart.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: c.text } },
      color: [c.blue, c.orange, c.green],
      series: [{
        type: 'pie', radius: ['45%', '68%'], center: ['50%', '44%'],
        label: { color: c.text, formatter: '{b}\n{c}' },
        data: [
          { name: '空置', value: s.vacant },
          { name: '已配租', value: s.occupied },
          { name: '其他', value: Math.max(0, s.total - s.vacant - s.occupied) }
        ]
      }]
    })
    charts.push(chart)
  }
  if (trendChart.value) {
    const rows = monthlyBills()
    const chart = echarts.init(trendChart.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { textStyle: { color: c.text } },
      grid: { left: 72, right: 18, top: 30, bottom: 30 },
      xAxis: { type: 'category', data: rows.map(r => r.key.slice(5)), axisLabel: { color: c.text }, axisLine: { lineStyle: { color: c.line } } },
      yAxis: { type: 'value', axisLabel: { color: c.text, formatter: v => Math.abs(v) >= 10000 ? (v / 10000).toFixed(1) + '万' : v }, splitLine: { lineStyle: { color: c.line } } },
      series: [
        { name: '应收', type: 'bar', barMaxWidth: 18, itemStyle: { color: c.blue }, data: rows.map(r => Number(r.amount.toFixed(2))) },
        { name: '已收', type: 'line', smooth: true, itemStyle: { color: c.green }, data: rows.map(r => Number(r.paid.toFixed(2))) }
      ]
    })
    charts.push(chart)
  }
  if (statusChart.value) {
    const statuses = ['UNPAID', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED']
    const statusLabels = { UNPAID: '未缴', PARTIAL: '部分缴', PAID: '已付', OVERDUE: '逾期', WAIVED: '已减免' }
    const chart = echarts.init(statusChart.value)
    chart.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: c.text } },
      color: [c.orange, c.purple, c.green, c.red, '#8c8c8c'],
      series: [{
        type: 'pie', radius: '62%', center: ['50%', '44%'],
        label: { color: c.text },
        data: statuses.map(s => ({ name: statusLabels[s], value: count(bills.value, s, 'billStatus') }))
      }]
    })
    charts.push(chart)
  }
  if (deviceChart.value) {
    const rows = deviceStats()
    const chart = echarts.init(deviceChart.value)
    chart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 92, right: 24, top: 10, bottom: 22 },
      xAxis: { type: 'value', axisLabel: { color: c.text }, splitLine: { lineStyle: { color: c.line } } },
      yAxis: { type: 'category', data: rows.map(r => r.name), axisLabel: { color: c.text } },
      series: [{ type: 'bar', barMaxWidth: 18, itemStyle: { color: c.blue }, data: rows.map(r => r.value) }]
    })
    charts.push(chart)
  }
}

async function loadSummary() {
  if (!project.value) return
  try {
    summary.value = await api.dashboardSummary(project.value.id, periodRange.value.start, periodRange.value.end)
  } catch (e) {
    summary.value = null
  }
}

function resize() { charts.forEach(c => c.resize()) }
watch(mode, () => nextTick(renderCharts))
watch([periodMode, customStart, customEnd], () => { loadSummary() })
onMounted(() => { load(); window.addEventListener('resize', resize) })
onBeforeUnmount(() => { window.removeEventListener('resize', resize); charts.forEach(c => c.dispose()) })
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>组织经营总览</h2><p>{{ orgSummary.projects }} 个项目 · 数据范围由当前角色决定</p></div><RouterLink to="/guarantee/reports">进入报表中心</RouterLink></div>
      <div class="grid cards" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">
        <div class="card"><div class="label">项目数</div><div class="value">{{ orgSummary.projects }}</div><div class="hint">当前数据范围</div></div>
        <div class="card"><div class="label">房源总数</div><div class="value">{{ orgSummary.houses }}</div><div class="hint">已出租 {{ orgSummary.rented }}</div></div>
        <div class="card"><div class="label">整体出租率</div><div class="value">{{ orgSummary.occupancy }}%</div><div class="hint">按项目汇总</div></div>
        <div class="card"><div class="label">应收</div><div class="value">¥{{ money(orgSummary.receivable) }}</div><div class="hint">全部项目</div></div>
        <div class="card"><div class="label">实收</div><div class="value">¥{{ money(orgSummary.received) }}</div><div class="hint">收缴率 {{ orgSummary.collection }}%</div></div>
        <div class="card"><div class="label">欠费</div><div class="value">¥{{ money(orgSummary.outstanding) }}</div><div class="hint">全部项目</div></div>
      </div>
      <div v-if="!rankedCompare.length" class="empty">暂无项目经营数据</div>
      <div v-else class="table-wrap" style="margin-top:12px"><table><thead><tr><th>项目</th><th>房源</th><th>出租率</th><th>应收</th><th>实收</th><th>收缴率</th><th>欠费</th><th>工单</th><th>操作</th></tr></thead><tbody>
        <tr v-for="p in rankedCompare" :key="p.projectId"><td><strong>{{ p.orgName }}</strong><div class="small muted">{{ p.orgCode }}</div></td><td>{{ p.houses }}</td><td>{{ p.occupancyRate }}%</td><td>¥{{ money(p.receivable) }}</td><td>¥{{ money(p.received) }}</td><td>{{ p.collectionRate }}%</td><td>¥{{ money(p.outstanding) }}</td><td>{{ p.workOrders }}</td><td><button class="sm" @click="focusProject(p.projectId)">查看</button></td></tr>
      </tbody></table></div>
    </div>

    <div class="panel">
      <div class="panel-head">
        <div><h2>运营驾驶舱</h2><p>{{ project?.orgName || '未选择项目' }} · 房源、合同、收费、设备概览</p></div>
        <div class="row">
          <select id="periodMode" v-model="periodMode" class="sm" style="padding:6px">
            <option value="month">本月账期</option>
            <option value="quarter">本季账期</option>
            <option value="year">本年账期</option>
            <option value="custom">自定义账期</option>
          </select>
          <template v-if="periodMode === 'custom'">
            <input v-model="customStart" type="date" class="sm" />
            <input v-model="customEnd" type="date" class="sm" />
          </template>
          <span class="badge blue">{{ periodRange.start }} ~ {{ periodRange.end }}</span>
        </div>
      </div>
      <div class="grid cards" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">
        <div class="card"><div class="label">项目数</div><div class="value">{{ projects.length }}</div><div class="hint">当前租户</div></div>
        <div class="card"><div class="label">保障房申请</div><div class="value">{{ applications.length }}</div><div class="hint">待审 {{ count(applications, 'SUBMITTED', 'applicationStatus') }}</div></div>
        <div class="card"><div class="label">生效合同</div><div class="value">{{ contracts.filter(c => c.contractStatus === 'ACTIVE').length }}</div><div class="hint">合同总数 {{ contracts.length }}</div></div>
        <div class="card clickable" @click="drillBilling"><div class="label">本期应收</div><div class="value">¥{{ money(billStats().total) }}</div><div class="hint">账期 {{ currentBills.length }} 笔</div></div>
        <div class="card clickable" @click="drillBilling"><div class="label">本期实收</div><div class="value">¥{{ money(billStats().paid) }}</div><div class="hint">按账单归属期</div></div>
        <div class="card clickable" @click="drillBilling"><div class="label">本期收缴率</div><div class="value">{{ billStats().rate }}%</div><div class="hint">当期欠费 ¥{{ money(billStats().outstanding) }}</div></div>
        <div class="card"><div class="label">期初欠费</div><div class="value">¥{{ money(billStats().opening) }}</div><div class="hint">期初回款 ¥{{ money(billStats().openingRecovery) }}</div></div>
        <div class="card clickable" @click="drillBilling"><div class="label">总欠费</div><div class="value">¥{{ money(billStats().totalOutstanding) }}</div><div class="hint">期初 + 当期</div></div>
        <div class="card"><div class="label">设备资产</div><div class="value">{{ devices.length }}</div><div class="hint">待处理告警 {{ alerts.filter(a => a.alertStatus === 'PENDING').length }} · 工单 {{ workOrders.filter(w => w.orderStatus === 'PENDING').length }}</div></div>
      </div>
    </div>

    <div class="alert" style="margin-top:10px">口径：本期应收/实收/收缴率按账期只算当期账单；期初欠费单独展示；总欠费 = 期初 + 当期。</div>
    <div class="grid" style="grid-template-columns:1.1fr 1.4fr">
      <div class="panel">
        <div class="panel-head"><h2>房源结构</h2><span class="small muted">共 {{ houses.length }} 套</span></div>
        <div ref="houseChart" class="chart" />
      </div>
      <div class="panel">
        <div class="panel-head"><h2>账单趋势</h2><span class="small muted">按账期月份</span></div>
        <div ref="trendChart" class="chart" />
      </div>
    </div>

    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="panel">
        <div class="panel-head"><h2>账单状态</h2><span class="small muted">{{ bills.length }} 笔</span></div>
        <div ref="statusChart" class="chart" />
      </div>
      <div class="panel">
        <div class="panel-head"><h2>设备类型</h2><span class="small muted">{{ devices.length }} 台</span></div>
        <div ref="deviceChart" class="chart" />
      </div>
    </div>

    <div class="grid" style="grid-template-columns:1.2fr .8fr">
      <div class="panel">
        <div class="panel-head"><h2>最近合同</h2><RouterLink to="/contracts">查看全部</RouterLink></div>
        <div v-if="!contracts.length" class="empty">暂无合同</div>
        <div v-for="c in contracts.slice(0, 5)" :key="c.id" class="row" style="border-bottom:1px solid var(--line);padding:9px 0">
          <div style="flex:1"><div>{{ c.contractNo }}</div><div class="small muted">{{ c.personName }} · {{ c.houseName }}</div></div>
          <span class="badge" :class="c.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ c.contractStatus }}</span>
          <span class="mono">¥{{ money(c.rentAmount) }}</span>
        </div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>待处理账单</h2><RouterLink to="/billing">去收款</RouterLink></div>
        <div v-if="!bills.length" class="empty">暂无账单</div>
        <div v-for="b in bills.filter(x => x.billStatus !== 'PAID').slice(0, 5)" :key="b.id" class="row" style="border-bottom:1px solid var(--line);padding:9px 0">
          <div style="flex:1"><div>{{ b.billNo }}</div><div class="small muted">{{ b.periodStart }} ~ {{ b.periodEnd }}</div></div>
          <span class="badge orange">{{ b.billStatus }}</span>
          <span class="mono">¥{{ money(b.payableAmount || b.amount) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
