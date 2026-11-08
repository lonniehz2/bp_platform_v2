<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { api } from '../api'
import { mode } from '../ui'

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
const houseChart = ref(null)
const trendChart = ref(null)
const statusChart = ref(null)
const deviceChart = ref(null)
let charts = []

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
const count = (list, status, field) => list.filter(x => x[field] === status).length
const rate = (a, b) => b ? Math.round(a / b * 1000) / 10 : 0

async function load() {
  loading.value = true; error.value = ''
  try {
    projects.value = await api.projects()
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
const billStats = () => {
  const total = bills.value.reduce((s, b) => s + Number(b.payableAmount || b.amount || 0), 0)
  const paid = bills.value.reduce((s, b) => s + Number(b.paidAmount || 0), 0)
  return { total, paid, outstanding: Math.max(0, total - paid), rate: rate(paid, total) }
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

function resize() { charts.forEach(c => c.resize()) }
watch(mode, () => nextTick(renderCharts))
onMounted(() => { load(); window.addEventListener('resize', resize) })
onBeforeUnmount(() => { window.removeEventListener('resize', resize); charts.forEach(c => c.dispose()) })
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head">
        <div><h2>运营驾驶舱</h2><p>{{ project?.orgName || '未选择项目' }} · 房源、合同、收费、设备概览</p></div>
        <span class="badge blue">{{ projects.length }} 个项目</span>
      </div>
      <div class="grid cards" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">
        <div class="card"><div class="label">项目数</div><div class="value">{{ projects.length }}</div><div class="hint">当前租户</div></div>
        <div class="card"><div class="label">保障房申请</div><div class="value">{{ applications.length }}</div><div class="hint">待审 {{ count(applications, 'SUBMITTED', 'applicationStatus') }}</div></div>
        <div class="card"><div class="label">生效合同</div><div class="value">{{ contracts.filter(c => c.contractStatus === 'ACTIVE').length }}</div><div class="hint">合同总数 {{ contracts.length }}</div></div>
        <div class="card"><div class="label">应收账单</div><div class="value">¥{{ money(billStats().total) }}</div><div class="hint">已收 ¥{{ money(billStats().paid) }}</div></div>
        <div class="card"><div class="label">收缴率</div><div class="value">{{ billStats().rate }}%</div><div class="hint">欠费 ¥{{ money(billStats().outstanding) }}</div></div>
        <div class="card"><div class="label">设备资产</div><div class="value">{{ devices.length }}</div><div class="hint">待处理告警 {{ alerts.filter(a => a.alertStatus === 'PENDING').length }} · 工单 {{ workOrders.filter(w => w.orderStatus === 'PENDING').length }}</div></div>
      </div>
    </div>

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
