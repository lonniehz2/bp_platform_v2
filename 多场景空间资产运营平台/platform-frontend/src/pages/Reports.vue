<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { sceneRoot } from '../scene'
import { useI18n } from 'vue-i18n'
import { api } from '../api'

const router = useRouter()
const { t, te } = useI18n()
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
const subscription = ref({ frequency: 'MONTHLY', recipients: '', enabled: false })
const subscriptions = ref([])
const error = ref('')
const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

const reports = [
  { key: 'projects', label: 'Project Performance' },
  { key: 'applications', label: 'Applications' },
  { key: 'contracts', label: 'Contracts' },
  { key: 'bills', label: 'Receivables' },
  { key: 'arrears', label: 'Arrears' },
  { key: 'houses', label: 'Houses' },
  { key: 'workOrders', label: 'Work Orders' },
  { key: 'devices', label: 'Devices' },
  { key: 'payments', label: 'Cash Flow' },
  { key: 'regulatory', label: 'Regulatory (project scope)' }
]

const columns = {
  projects: [['orgName','Project'],['houses','Houses'],['occupancyRate','Occupancy'],['receivable','Receivable'],['received','Received'],['collectionRate','Collection Rate'],['outstanding','Outstanding'],['workOrders','Work Orders']],
  applications: [['applicationNo','Application No.'],['applicantName','Applicant'],['applicationType','Type'],['familySize','Family Size'],['applicationStatus','Status']],
  contracts: [['contractNo','Contract No.'],['personName','Tenant'],['houseName','House'],['startDate','Start'],['endDate','End'],['rentAmount','Rent'],['contractStatus','Status']],
  bills: [['billNo','Bill No.'],['personName','Tenant'],['periodStart','Period Start'],['periodEnd','Period End'],['payableAmount','Payable'],['paidAmount','Paid'],['billStatus','Status']],
  houses: [['houseCode','House Code'],['houseName','Name'],['area','Area'],['layoutType','Layout'],['houseStatus','House Status']],
  workOrders: [['orderNo','Order No.'],['title','Title'],['orderType','Type'],['assigneeName','Assignee'],['orderStatus','Status']],
  devices: [['deviceCode','Device Code'],['deviceName','Name'],['deviceType','Type'],['businessStatus','Business Status']],
  payments: [['paymentNo','Payment No.'],['paymentMethod','Method'],['amount','Amount'],['paidTime','Time'],['paymentStatus','Status']],
  regulatory: [['orgName','Project'],['houses','Total Houses'],['rentedHouses','Rented'],['vacantHouses','Vacant'],['occupancyRate','Occupancy'],['activeContracts','Active Contracts'],['receivable','Receivable'],['received','Received'],['outstanding','Outstanding']]
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
const title = computed(() => reports.find(r => r.key === active.value)?.label || 'Reports')

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
  if (key.toLowerCase().includes('status')) { const code = String(v).toUpperCase(); return te(`status.${code}`) ? t(`status.${code}`) : v }
  if (['receivable','received','outstanding','amount','payableAmount','paidAmount','rentAmount'].includes(key)) return '¥' + money(v)
  if (['occupancyRate','collectionRate'].includes(key)) return v + '%'
  return v
}

function exportRow(row) {
  const header = cols.value.map(c => c[1])
  const data = [cols.value.map(([key]) => row[key] ?? '')]
  const csv = '\ufeff' + [header, ...data].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const link = document.createElement('a')
  link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  link.download = `${t('reports.title')}_${title.value}_${row.orgName || row.contractNo || 'row'}.csv`
  link.click(); URL.revokeObjectURL(link.href)
}

function exportCsv() {
  const header = cols.value.map(c => c[1])
  const data = filteredRows.value.map(row => cols.value.map(([key]) => row[key] ?? ''))
  const csv = '\ufeff' + [header, ...data].map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `${t('reports.title')}_${title.value}.csv`
  link.click(); URL.revokeObjectURL(link.href)
}

watch(active, key => { statusFilter.value = ''; applySaved(key) })
function openProject(row) { localStorage.setItem('platformProjectId', String(row.projectId)); router.push(sceneRoot() + '/cockpit') }
function saveSubscription() {
  if (!subscription.value.recipients.trim()) { error.value = t('reports.recipientsRequired'); return }
  subscriptions.value = [...subscriptions.value, { report: title.value, frequency: subscription.value.frequency, recipients: subscription.value.recipients.trim(), enabled: subscription.value.enabled }]
  localStorage.setItem('platformReportSubscriptions', JSON.stringify(subscriptions.value))
  subscription.value = { frequency: 'MONTHLY', recipients: '', enabled: false }
}

onMounted(() => { try { savedViews.value = JSON.parse(localStorage.getItem('platformReportViews') || '{}') } catch {}
  try { subscriptions.value = JSON.parse(localStorage.getItem('platformReportSubscriptions') || '[]') } catch {}
  load() })
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('reports.title') }}</h2><p>{{ project?.orgName || t('common.project') }} · {{ t('reports.subtitle') }}</p></div><button class="primary" @click="exportCsv">{{ t('reports.export') }}</button></div>
      <div class="tab-strip">
        <button v-for="r in reports" :key="r.key" class="tab-btn" :class="{ active: active === r.key }" @click="active = r.key">{{ te(`report.${r.key}`) ? t(`report.${r.key}`) : r.label }}</button>
      </div>
      <div class="row" style="justify-content:space-between;align-items:center;margin:8px 0">
        <strong>{{ te(`report.${active}`) ? t(`report.${active}`) : title }}</strong><span class="small muted">{{ filteredRows.length }} {{ t('reports.records') }}</span>
      </div>
      <div v-if="active === 'regulatory'" class="alert">{{ t('reports.regulatoryNote') }}</div>
      <div class="row" style="margin-bottom:8px">
        <input v-model="search" :placeholder="t('reports.search')" style="max-width:260px" />
        <select v-if="statusOptions.length" v-model="statusFilter" style="max-width:160px"><option value="">{{ t('reports.allStatus') }}</option><option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option></select>
        <button class="sm" @click="saveView">{{ t('reports.save') }}</button>
        <button class="sm" @click="resetFilters">{{ t('reports.reset') }}</button>
      </div>
      <div v-if="!filteredRows.length" class="empty">{{ t('reports.noData') }}</div>
      <div v-else class="table-wrap">
        <table><thead><tr><th v-for="c in cols" :key="c[0]">{{ te(`field.${c[0]}`) ? t(`field.${c[0]}`) : c[1] }}</th><th v-if="active === 'projects'">{{ t('common.action') }}</th></tr></thead><tbody>
          <tr v-for="(row, i) in filteredRows" :key="i"><td v-for="c in cols" :key="c[0]">{{ display(row, c[0]) }}</td><td v-if="active === 'projects'"><button class="sm" @click="exportRow(row)">{{ t('reports.download') }}</button></td></tr>
        </tbody></table>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('reports.subscription') }}</h2><p>{{ t('reports.subscriptionHint') }}</p></div></div>
      <div class="row">
        <div class="field"><label>{{ t('reports.frequency') }}</label><select v-model="subscription.frequency"><option value="DAILY">{{ t('reports.daily') }}</option><option value="WEEKLY">{{ t('reports.weekly') }}</option><option value="MONTHLY">{{ t('reports.monthly') }}</option></select></div>
        <div class="field" style="flex:2"><label>{{ t('reports.recipients') }}</label><input v-model="subscription.recipients" :placeholder="t('reports.recipients')" /></div>
        <div class="field"><label>{{ t('reports.enabled') }}</label><input v-model="subscription.enabled" type="checkbox" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" @click="saveSubscription">{{ t('reports.saveSubscription') }}</button></div>
      </div>
      <div v-if="subscriptions.length" class="table-wrap"><table><thead><tr><th>{{ t('reports.report') }}</th><th>{{ t('reports.frequency') }}</th><th>{{ t('reports.recipients') }}</th><th>{{ t('reports.status') }}</th></tr></thead><tbody><tr v-for="(s, i) in subscriptions" :key="i"><td>{{ s.report }}</td><td>{{ s.frequency }}</td><td>{{ s.recipients }}</td><td>{{ s.enabled ? t('reports.enabled') : t('status.DISABLED') }}</td></tr></tbody></table></div>
      <div v-else class="empty">{{ t('reports.noData') }}</div>
    </div>
  </div>
</template>

<style scoped>
.tab-strip{display:flex;gap:6px;border-bottom:1px solid var(--line);overflow-x:auto}
.tab-btn{border:0;background:transparent;padding:8px 10px;border-bottom:2px solid transparent;color:var(--muted);cursor:pointer;white-space:nowrap}
.tab-btn.active{color:var(--brand);border-bottom-color:var(--brand);font-weight:600}
</style>
