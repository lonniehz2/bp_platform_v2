<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { currentScene, sceneRoot } from '../scene'
import * as echarts from 'echarts'
import { api } from '../api'
import { mode } from '../ui'

const router = useRouter()
const { t } = useI18n()
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
const user = (() => { try { return JSON.parse(localStorage.getItem('platformUser') || '{}') } catch { return {} } })()
const scene = currentScene()
const isManager = (user.roles || []).some(r => ['ADMIN', `${scene}_ADMIN`, `${scene}_MANAGER`].includes(r))
const cockpitView = ref(isManager ? 'org' : 'project')
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
  const labels = { LOCK: t('field.deviceType'), METER: t('field.deviceType'), WATER_METER: t('field.deviceType'), ELEC_METER: t('field.deviceType'), ELECTRICITY_METER: t('field.deviceType'), GAS_METER: t('field.deviceType'), ELEVATOR: t('field.deviceType'), GATE: t('field.deviceType') }
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
          { name: t('ops.vacant'), value: s.vacant },
          { name: t('ops.allocated'), value: s.occupied },
          { name: t('ops.other'), value: Math.max(0, s.total - s.vacant - s.occupied) }
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
      yAxis: { type: 'value', axisLabel: { color: c.text, formatter: v => Math.abs(v) >= 10000 ? (v / 10000).toFixed(1) + t('ops.tenThousand') : v }, splitLine: { lineStyle: { color: c.line } } },
      series: [
        { name: t('ops.receivable'), type: 'bar', barMaxWidth: 18, itemStyle: { color: c.blue }, data: rows.map(r => Number(r.amount.toFixed(2))) },
        { name: t('ops.received'), type: 'line', smooth: true, itemStyle: { color: c.green }, data: rows.map(r => Number(r.paid.toFixed(2))) }
      ]
    })
    charts.push(chart)
  }
  if (statusChart.value) {
    const statuses = ['UNPAID', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED']
    const statusLabels = { UNPAID: t('status.UNPAID'), PARTIAL: t('status.PARTIAL'), PAID: t('status.PAID'), OVERDUE: t('status.EXPIRED'), WAIVED: t('status.WAIVED') }
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
      <div class="panel-head"><div><h2>{{ t('cockpit.org') }}</h2><p>{{ orgSummary.projects }} {{ t('cockpit.projects') }} · {{ t('cockpit.currentScope') }}</p></div><div class="row"><button class="sm" :class="{ primary: cockpitView === 'org' }" @click="cockpitView = 'org'">{{ t('cockpit.orgView') }}</button><button class="sm" :class="{ primary: cockpitView === 'project' }" @click="cockpitView = 'project'">{{ t('cockpit.projectView') }}</button><RouterLink :to="sceneRoot() + '/reports'">{{ t('cockpit.reports') }}</RouterLink></div></div>
      <template v-if="cockpitView === 'org'">
      <div class="grid cards" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">
        <div class="card"><div class="label">{{ t('cockpit.projects') }}</div><div class="value">{{ orgSummary.projects }}</div><div class="hint">{{ t('cockpit.currentScope') }}</div></div>
        <div class="card"><div class="label">{{ t('cockpit.houses') }}</div><div class="value">{{ orgSummary.houses }}</div><div class="hint">{{ t('cockpit.rented') }} {{ orgSummary.rented }}</div></div>
        <div class="card"><div class="label">{{ t('cockpit.occupancy') }}</div><div class="value">{{ orgSummary.occupancy }}%</div><div class="hint">{{ t('cockpit.byProject') }}</div></div>
        <div class="card"><div class="label">{{ t('cockpit.receivable') }}</div><div class="value">¥{{ money(orgSummary.receivable) }}</div><div class="hint">{{ t('cockpit.allProjects') }}</div></div>
        <div class="card"><div class="label">{{ t('cockpit.received') }}</div><div class="value">¥{{ money(orgSummary.received) }}</div><div class="hint">{{ t('cockpit.collection') }} {{ orgSummary.collection }}%</div></div>
        <div class="card"><div class="label">{{ t('cockpit.outstanding') }}</div><div class="value">¥{{ money(orgSummary.outstanding) }}</div><div class="hint">{{ t('cockpit.allProjects') }}</div></div>
      </div>
      <div v-if="!rankedCompare.length" class="empty">{{ t('ops.emptyProjects') }}</div>
      <div v-else class="table-wrap" style="margin-top:12px"><table><thead><tr><th>{{ t('ops.project') }}</th><th>{{ t('ops.house') }}</th><th>{{ t('ops.occupancy') }}</th><th>{{ t('cockpit.receivable') }}</th><th>{{ t('cockpit.received') }}</th><th>{{ t('cockpit.collection') }}</th><th>{{ t('cockpit.outstanding') }}</th><th>{{ t('ops.workOrders') }}</th><th>{{ t('common.action') }}</th></tr></thead><tbody>
        <tr v-for="p in rankedCompare" :key="p.projectId"><td><strong>{{ p.orgName }}</strong><div class="small muted">{{ p.orgCode }}</div></td><td>{{ p.houses }}</td><td>{{ p.occupancyRate }}%</td><td>¥{{ money(p.receivable) }}</td><td>¥{{ money(p.received) }}</td><td>{{ p.collectionRate }}%</td><td>¥{{ money(p.outstanding) }}</td><td>{{ p.workOrders }}</td><td><button class="sm" @click="focusProject(p.projectId)">{{ t('cockpit.view') }}</button></td></tr>
      </tbody></table></div>
      </template>
    </div>

    <div class="panel">
      <div class="panel-head">
        <div><h2>{{ t('cockpit.projectCockpit') }}</h2><p>{{ project?.orgName || t('ops.noProject') }} · {{ t('cockpit.projectHint') }}</p></div>
        <div class="row">
          <select id="periodMode" v-model="periodMode" class="sm" style="padding:6px">
            <option value="month">{{ t('ops.thisMonth') }}</option>
            <option value="quarter">{{ t('ops.thisQuarter') }}</option>
            <option value="year">{{ t('ops.thisYear') }}</option>
            <option value="custom">{{ t('ops.customPeriod') }}</option>
          </select>
          <template v-if="periodMode === 'custom'">
            <input v-model="customStart" type="date" class="sm" />
            <input v-model="customEnd" type="date" class="sm" />
          </template>
          <span class="badge blue">{{ periodRange.start }} ~ {{ periodRange.end }}</span>
        </div>
      </div>
      <div class="grid cards" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr))">
        <div class="card"><div class="label">{{ t('cockpit.projects') }}</div><div class="value">{{ projects.length }}</div><div class="hint">{{ t('ops.tenant') }}</div></div>
        <div class="card"><div class="label">{{ t('ops.applications') }}</div><div class="value">{{ applications.length }}</div><div class="hint">{{ t('ops.pendingReview') }} {{ count(applications, 'SUBMITTED', 'applicationStatus') }}</div></div>
        <div class="card"><div class="label">{{ t('ops.activeContracts') }}</div><div class="value">{{ contracts.filter(c => c.contractStatus === 'ACTIVE').length }}</div><div class="hint">{{ t('ops.totalContracts') }} {{ contracts.length }}</div></div>
        <div class="card clickable" @click="drillBilling"><div class="label">{{ t('ops.currentReceivable') }}</div><div class="value">¥{{ money(billStats().total) }}</div><div class="hint">{{ t('ops.periodBills') }} {{ currentBills.length }} {{ t('ops.billsUnit') }}</div></div>
        <div class="card clickable" @click="drillBilling"><div class="label">{{ t('ops.currentReceived') }}</div><div class="value">¥{{ money(billStats().paid) }}</div><div class="hint">{{ t('ops.byPeriod') }}</div></div>
        <div class="card clickable" @click="drillBilling"><div class="label">{{ t('ops.currentCollection') }}</div><div class="value">{{ billStats().rate }}%</div><div class="hint">{{ t('ops.currentArrears') }} ¥{{ money(billStats().outstanding) }}</div></div>
        <div class="card"><div class="label">{{ t('ops.openingArrears') }}</div><div class="value">¥{{ money(billStats().opening) }}</div><div class="hint">{{ t('ops.openingRecovery') }} ¥{{ money(billStats().openingRecovery) }}</div></div>
        <div class="card clickable" @click="drillBilling"><div class="label">{{ t('ops.totalArrears') }}</div><div class="value">¥{{ money(billStats().totalOutstanding) }}</div><div class="hint">{{ t('ops.openingPlusCurrent') }}</div></div>
        <div class="card"><div class="label">{{ t('ops.devices') }}</div><div class="value">{{ devices.length }}</div><div class="hint">{{ t('ops.pendingAlerts') }} {{ alerts.filter(a => a.alertStatus === 'PENDING').length }} · {{ t('ops.workOrders') }} {{ workOrders.filter(w => w.orderStatus === 'PENDING').length }}</div></div>
      </div>
    </div>

    <div class="alert" style="margin-top:10px">{{ t('ops.caliber') }}</div>
    <div class="grid" style="grid-template-columns:1.1fr 1.4fr">
      <div class="panel">
        <div class="panel-head"><h2>{{ t('ops.houseStructure') }}</h2><span class="small muted">{{ t('ops.totalHouses') }} {{ houses.length }} {{ t('ops.houseUnit') }}</span></div>
        <div ref="houseChart" class="chart" />
      </div>
      <div class="panel">
        <div class="panel-head"><h2>{{ t('ops.billTrend') }}</h2><span class="small muted">{{ t('ops.byMonth') }}</span></div>
        <div ref="trendChart" class="chart" />
      </div>
    </div>

    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="panel">
        <div class="panel-head"><h2>{{ t('ops.billStatus') }}</h2><span class="small muted">{{ bills.length }} {{ t('ops.billsUnit') }}</span></div>
        <div ref="statusChart" class="chart" />
      </div>
      <div class="panel">
        <div class="panel-head"><h2>{{ t('ops.deviceTypes') }}</h2><span class="small muted">{{ devices.length }} {{ t('ops.deviceUnit') }}</span></div>
        <div ref="deviceChart" class="chart" />
      </div>
    </div>

    <div class="grid" style="grid-template-columns:1.2fr .8fr">
      <div class="panel">
        <div class="panel-head"><h2>{{ t('ops.recentContracts') }}</h2><RouterLink to="/contracts">{{ t('ops.viewAll') }}</RouterLink></div>
        <div v-if="!contracts.length" class="empty">{{ t('ops.noContracts') }}</div>
        <div v-for="c in contracts.slice(0, 5)" :key="c.id" class="row" style="border-bottom:1px solid var(--line);padding:9px 0">
          <div style="flex:1"><div>{{ c.contractNo }}</div><div class="small muted">{{ c.personName }} · {{ c.houseName }}</div></div>
          <span class="badge" :class="c.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ c.contractStatus }}</span>
          <span class="mono">¥{{ money(c.rentAmount) }}</span>
        </div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>{{ t('ops.pendingBills') }}</h2><RouterLink to="/billing">{{ t('ops.collect') }}</RouterLink></div>
        <div v-if="!bills.length" class="empty">{{ t('ops.noBills') }}</div>
        <div v-for="b in bills.filter(x => x.billStatus !== 'PAID').slice(0, 5)" :key="b.id" class="row" style="border-bottom:1px solid var(--line);padding:9px 0">
          <div style="flex:1"><div>{{ b.billNo }}</div><div class="small muted">{{ b.periodStart }} ~ {{ b.periodEnd }}</div></div>
          <span class="badge orange">{{ b.billStatus }}</span>
          <span class="mono">¥{{ money(b.payableAmount || b.amount) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
