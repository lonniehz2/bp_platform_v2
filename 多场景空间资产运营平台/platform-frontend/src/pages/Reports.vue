<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api'

const project = ref(null)
const compare = ref([])
const applications = ref([])
const contracts = ref([])
const bills = ref([])
const payments = ref([])
const devices = ref([])
const houses = ref([])
const workOrders = ref([])
const alerts = ref([])
const active = ref('projects')
const search = ref('')
const statusFilter = ref('')
const savedViews = ref({})
const error = ref('')
const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

const reports = [
  { key: 'projects', label: '项目经营对比' },
  { key: 'applications', label: '申请受理' },
  { key: 'contracts', label: '合同台账' },
  { key: 'bills', label: '应收实收' },
  { key: 'arrears', label: '欠费清单' },
  { key: 'houses', label: '房源台账' },
  { key: 'workOrders', label: '工单统计' },
  { key: 'devices', label: '设备台账' },
  { key: 'payments', label: '资金流水' },
  { key: 'regulatory', label: '监管报送' }
]

const columns = {
  projects: [['orgName','项目'],['houses','房源'],['occupancyRate','出租率'],['receivable','应收'],['received','实收'],['collectionRate','收缴率'],['outstanding','欠费'],['workOrders','工单']],
  applications: [['applicationNo','申请编号'],['applicantName','申请人'],['applicationType','类型'],['familySize','家庭人数'],['applicationStatus','状态']],
  contracts: [['contractNo','合同号'],['personName','承租人'],['houseName','房屋'],['startDate','开始'],['endDate','结束'],['rentAmount','租金'],['contractStatus','状态']],
  bills: [['billNo','账单号'],['personName','承租人'],['periodStart','账期起'],['periodEnd','账期止'],['payableAmount','应付'],['paidAmount','已收'],['billStatus','状态']],
  houses: [['houseCode','房源编码'],['houseName','名称'],['area','面积'],['layoutType','户型'],['houseStatus','房态']],
  workOrders: [['orderNo','工单号'],['title','标题'],['orderType','类型'],['assigneeName','处理人'],['orderStatus','状态']],
  devices: [['deviceCode','设备编码'],['deviceName','名称'],['deviceType','类型'],['businessStatus','业务状态']],
  payments: [['paymentNo','收款单号'],['paymentMethod','方式'],['amount','金额'],['paidTime','时间'],['paymentStatus','状态']],
  regulatory: [['orgName','项目'],['houses','房源'],['occupancyRate','出租率'],['receivable','应收'],['received','实收'],['outstanding','欠费']]
}
const rows = computed(() => ({
  projects: compare.value,
  applications: applications.value,
  contracts: contracts.value,
  bills: bills.value,
  arrears: bills.value.filter(b => b.billStatus !== 'PAID'),
  houses: houses.value,
  workOrders: workOrders.value,
  devices: devices.value,
  payments: payments.value,
  regulatory: compare.value
}[active.value] || []))
const cols = computed(() => columns[active.value] || [])
const statusKeys = { applications: 'applicationStatus', contracts: 'contractStatus', bills: 'billStatus', arrears: 'billStatus', houses: 'houseStatus', workOrders: 'orderStatus', devices: 'businessStatus', payments: 'paymentStatus' }
const statusOptions = computed(() => {
  const key = statusKeys[active.value]
  if (!key) return []
  return [...new Set((rows.value || []).map(r => r[key]).filter(Boolean))].sort()
})
const filteredRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  const key = statusKeys[active.value]
  return rows.value.filter(r => {
    if (statusFilter.value && key && String(r[key] || '') !== statusFilter.value) return false
    if (!q) return true
    return Object.values(r).some(v => String(v ?? '').toLowerCase().includes(q))
  })
})
function saveView() {
  const next = { ...savedViews.value, [active.value]: { search: search.value, status: statusFilter.value } }
  savedViews.value = next; localStorage.setItem('platformReportViews', JSON.stringify(next))
}
function applySaved(key) { const v = savedViews.value[key]; if (!v) return; search.value = v.search || ''; statusFilter.value = v.status || '' }
function resetFilters() { search.value = ''; statusFilter.value = '' }
const title = computed(() => reports.find(r => r.key === active.value)?.label || '报表')

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    compare.value = await api.reportCompare()
    if (!project.value) return
    const id = project.value.id
    const [a, c, b, p, d, h, w, al] = await Promise.all([
      api.applications(id), api.contracts(id), api.bills(id), api.payments(id),
      api.devices(id), api.houses(id), api.workOrders(id), api.alerts(id)
    ])
    applications.value = a; contracts.value = c; bills.value = b; payments.value = p
    devices.value = d; houses.value = h; workOrders.value = w; alerts.value = al
  } catch (e) { error.value = e.message }
}

function display(row, key) {
  const v = row[key]
  if (v === null || v === undefined || v === '') return '-'
  if (['receivable','received','outstanding','amount','payableAmount','paidAmount','rentAmount'].includes(key)) return '¥' + money(v)
  if (['occupancyRate','collectionRate'].includes(key)) return v + '%'
  return v
}

function exportCsv() {
  const header = cols.value.map(c => c[1])
  const data = filteredRows.value.map(row => cols.value.map(([key]) => row[key] ?? ''))
  const csv = '\ufeff' + [header, ...data].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `报表_${title.value}.csv`
  link.click(); URL.revokeObjectURL(link.href)
}

watch(active, key => { statusFilter.value = ''; applySaved(key) })
onMounted(() => { try { savedViews.value = JSON.parse(localStorage.getItem('platformReportViews') || '{}') } catch {}; load() })
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>报表中心</h2><p>{{ project?.orgName || '未选择项目' }} · 经营明细与监管数据</p></div><button class="primary" @click="exportCsv">导出当前报表</button></div>
      <div class="tab-strip">
        <button v-for="r in reports" :key="r.key" class="tab-btn" :class="{ active: active === r.key }" @click="active = r.key">{{ r.label }}</button>
      </div>
      <div class="row" style="justify-content:space-between;align-items:center;margin:8px 0">
        <strong>{{ title }}</strong><span class="small muted">共 {{ filteredRows.length }} 条</span>
      </div>
      <div class="row" style="margin-bottom:8px">
        <input v-model="search" placeholder="搜索当前报表" style="max-width:260px" />
        <select v-if="statusOptions.length" v-model="statusFilter" style="max-width:160px"><option value="">全部状态</option><option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option></select>
        <button class="sm" @click="saveView">保存筛选</button>
        <button class="sm" @click="resetFilters">重置</button>
      </div>
      <div v-if="!filteredRows.length" class="empty">暂无数据</div>
      <div v-else class="table-wrap">
        <table><thead><tr><th v-for="c in cols" :key="c[0]">{{ c[1] }}</th></tr></thead><tbody>
          <tr v-for="(row, i) in filteredRows" :key="i"><td v-for="c in cols" :key="c[0]">{{ display(row, c[0]) }}</td></tr>
        </tbody></table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-strip{display:flex;gap:6px;border-bottom:1px solid var(--line);overflow-x:auto}
.tab-btn{border:0;background:transparent;padding:8px 10px;border-bottom:2px solid transparent;color:var(--muted);cursor:pointer;white-space:nowrap}
.tab-btn.active{color:var(--brand);border-bottom-color:var(--brand);font-weight:600}
</style>
