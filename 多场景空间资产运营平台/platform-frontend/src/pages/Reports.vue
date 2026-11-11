<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
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
  { key: 'projects', label: '项目经营对比' },
  { key: 'applications', label: '申请受理' },
  { key: 'contracts', label: '合同台账' },
  { key: 'bills', label: '应收实收' },
  { key: 'arrears', label: '欠费清单' },
  { key: 'houses', label: '房源台账' },
  { key: 'workOrders', label: '工单统计' },
  { key: 'devices', label: '设备台账' },
  { key: 'payments', label: '资金流水' },
  { key: 'regulatory', label: '监管报送（项目口径）' }
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
  regulatory: [['orgName','项目'],['houses','房源总数'],['rentedHouses','已出租'],['vacantHouses','空置'],['occupancyRate','出租率'],['activeContracts','在租合同'],['receivable','应收'],['received','实收'],['outstanding','欠费']]
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
function openProject(row) { localStorage.setItem('platformProjectId', String(row.projectId)); router.push('/guarantee/cockpit') }
function saveSubscription() {
  if (!subscription.value.recipients.trim()) { error.value = '请填写订阅接收人'; return }
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
      <div v-if="active === 'regulatory'" class="alert">监管口径：房源总数、已出租、空置、出租率、在租合同、应收、实收、欠费；按项目汇总。</div>
      <div class="row" style="margin-bottom:8px">
        <input v-model="search" :placeholder="t('reports.search')" style="max-width:260px" />
        <select v-if="statusOptions.length" v-model="statusFilter" style="max-width:160px"><option value="">{{ t('reports.allStatus') }}</option><option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option></select>
        <button class="sm" @click="saveView">{{ t('reports.save') }}</button>
        <button class="sm" @click="resetFilters">{{ t('reports.reset') }}</button>
      </div>
      <div v-if="!filteredRows.length" class="empty">{{ t('reports.noData') }}</div>
      <div v-else class="table-wrap">
        <table><thead><tr><th v-for="c in cols" :key="c[0]">{{ te(`field.${c[0]}`) ? t(`field.${c[0]}`) : c[1] }}</th><th v-if="active === 'projects'">操作</th></tr></thead><tbody>
          <tr v-for="(row, i) in filteredRows" :key="i"><td v-for="c in cols" :key="c[0]">{{ display(row, c[0]) }}</td><td v-if="active === 'projects'"><button class="sm" @click="openProject(row)">{{ t('reports.drill') }}</button></td></tr>
        </tbody></table>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('reports.subscription') }}</h2><p>{{ t('reports.subscriptionHint') }}</p></div></div>
      <div class="row">
        <div class="field"><label>{{ t('reports.frequency') }}</label><select v-model="subscription.frequency"><option value="DAILY">{{ t('reports.daily') }}</option><option value="WEEKLY">{{ t('reports.weekly') }}</option><option value="MONTHLY">{{ t('reports.monthly') }}</option></select></div>
        <div class="field" style="flex:2"><label>{{ t('reports.recipients') }}</label><input v-model="subscription.recipients" placeholder="用户名或邮箱" /></div>
        <div class="field"><label>{{ t('reports.enabled') }}</label><input v-model="subscription.enabled" type="checkbox" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" @click="saveSubscription">{{ t('reports.saveSubscription') }}</button></div>
      </div>
      <div v-if="subscriptions.length" class="table-wrap"><table><thead><tr><th>报表</th><th>{{ t('reports.frequency') }}</th><th>{{ t('reports.recipients') }}</th><th>状态</th></tr></thead><tbody><tr v-for="(s, i) in subscriptions" :key="i"><td>{{ s.report }}</td><td>{{ s.frequency }}</td><td>{{ s.recipients }}</td><td>{{ s.enabled ? '启用' : '停用' }}</td></tr></tbody></table></div>
      <div v-else class="empty">暂无订阅</div>
    </div>
  </div>
</template>

<style scoped>
.tab-strip{display:flex;gap:6px;border-bottom:1px solid var(--line);overflow-x:auto}
.tab-btn{border:0;background:transparent;padding:8px 10px;border-bottom:2px solid transparent;color:var(--muted);cursor:pointer;white-space:nowrap}
.tab-btn.active{color:var(--brand);border-bottom-color:var(--brand);font-weight:600}
</style>
