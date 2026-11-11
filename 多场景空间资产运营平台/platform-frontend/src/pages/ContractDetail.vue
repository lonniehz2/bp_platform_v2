<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import { can } from '../permissions'
import { contractStatusLabel, contractStatusTone } from '../contractStatus'
import { relationLabel, relationStatusLabel } from '../relationLabels'
import SearchSelect from '../components/SearchSelect.vue'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()
const router = useRouter()
const contract = ref(null)
const error = ref('')
const busy = ref(false)
const tab = ref(['overview','persons','house','bills','deposit','files','changes'].includes(String(route.query.tab)) ? String(route.query.tab) : 'overview')
const cohabitants = ref([])
const bills = ref([])
const deposit = ref(null)
const subsidies = ref([])
const files = ref([])
const changes = ref([])
const loaded = ref({})
const fileBusy = ref(false)
const persons = ref([])
const cohabForm = reactive({ personId: '', relationType: 'FAMILY', startDate: '', endDate: '' })

const tabs = computed(() => [
  { key: 'overview', label: t('cd.overview') },
  { key: 'persons', label: t('cd.persons') },
  { key: 'house', label: t('cd.house') },
  can('billing') ? { key: 'bills', label: t('cd.bills') } : null,
  can('deposits') ? { key: 'deposit', label: t('cd.deposit') } : null,
  { key: 'files', label: t('cd.files') },
  { key: 'changes', label: t('cd.changes') }
].filter(Boolean))

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function load() {
  error.value = ''
  loaded.value = {}
  cohabitants.value = []; bills.value = []; deposit.value = null; subsidies.value = []; files.value = []; changes.value = []
  try {
    const projects = await api.projects()
    const saved = localStorage.getItem('platformProjectId')
    const ordered = [
      ...projects.filter(p => String(p.id) === String(saved)),
      ...projects.filter(p => String(p.id) !== String(saved))
    ]
    contract.value = null
    for (const project of ordered) {
      const list = await api.contracts(project.id)
      const found = list.find(c => String(c.id) === String(route.params.id))
      if (found) { contract.value = found; break }
    }
    if (!contract.value) throw new Error(t('cd.missing'))
    await preload()
  } catch (e) { error.value = e.message }
}

async function preload() {
  if (!contract.value) return
  const allowed = new Set(tabs.value.map(t => t.key))
  const jobs = []
  if (allowed.has('persons')) jobs.push(loadSection('persons'))
  if (allowed.has('bills')) jobs.push(loadSection('bills'))
  if (allowed.has('deposit')) jobs.push(loadSection('deposit'))
  if (allowed.has('files')) jobs.push(loadSection('files'))
  if (allowed.has('changes')) jobs.push(loadSection('changes'))
  await Promise.all(jobs)
}

async function loadSection(key) {
  if (!contract.value || loaded.value[key]) return
  try {
    if (key === 'persons') {
      cohabitants.value = await api.cohabitants(contract.value.id)
      if (!persons.value.length) persons.value = await api.persons()
      if (!cohabForm.personId && persons.value.length) cohabForm.personId = persons.value[0].id
    }
    if (key === 'bills') bills.value = await api.contractBills(contract.value.id)
    if (key === 'deposit') { deposit.value = await api.deposit(contract.value.id); subsidies.value = await api.subsidies(contract.value.id) }
    if (key === 'files') files.value = await api.files('CONTRACT', contract.value.id)
    if (key === 'changes') changes.value = await api.changes(contract.value.id)
  } catch (e) { /* Keep unauthorized tabs empty without blocking others */ }
  loaded.value[key] = true
}

async function loadTab() {
  if (!contract.value) return
  await loadSection(tab.value)
}


async function addCohabitant() {
  if (!cohabForm.personId) { error.value = t('cd.required'); return }
  busy.value = true; error.value = ''
  try {
    await api.addCohabitant(contract.value.id, {
      personId: cohabForm.personId,
      relationType: cohabForm.relationType,
      startDate: cohabForm.startDate || null,
      endDate: cohabForm.endDate || null,
      remark: ''
    })
    cohabitants.value = await api.cohabitants(contract.value.id)
    cohabForm.personId = ''
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function removeCohabitant(c) {
  busy.value = true; error.value = ''
  try {
    await api.removeCohabitant(c.id)
    cohabitants.value = await api.cohabitants(contract.value.id)
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function uploadFile(event) {
  const file = event.target.files?.[0]
  if (!file || !contract.value) return
  fileBusy.value = true
  try {
    await api.uploadFile('CONTRACT', contract.value.id, file)
    files.value = await api.files('CONTRACT', contract.value.id)
    loaded.value.files = true
  } catch (e) { error.value = e.message } finally { fileBusy.value = false; event.target.value = '' }
}

function switchTab(key) {
  tab.value = key
  router.replace({ query: { ...route.query, tab: key } })
}

function openPerson(id) { if (id) router.push(`/guarantee/persons?id=${id}&from=contract&contractId=${contract.value.id}`) }
function openHouse(id) { if (id) router.push(`/guarantee/houses?id=${id}&from=contract&contractId=${contract.value.id}`) }

onMounted(load)
watch(() => route.params.id, load)
watch(tab, loadTab)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!contract" class="panel"><div class="empty">{{ t('cd.loading') }}</div></div>
    <template v-else>
      <div class="panel contract-head">
        <div class="panel-head">
          <div>
            <h2>{{ contract.contractNo }}</h2>
            <p>{{ contract.personName }} · {{ contract.houseName }} · {{ contract.startDate }} ~ {{ contract.endDate }}</p>
          </div>
          <div class="row"><span class="badge" :class="contractStatusTone(contract.contractStatus)">{{ contractStatusLabel(contract.contractStatus) }}</span><button class="sm" @click="router.push('/guarantee/contracts')">{{ t('cd.back') }}</button></div>
        </div>
        <div class="summary">
          <div><span>{{ t('cd.rent') }}</span><strong>{{ money(contract.rentAmount) }}</strong></div>
          <div><span>{{ t('cd.depositAmount') }}</span><strong>{{ money(contract.depositAmount) }}</strong></div>
          <div><span>{{ t('cd.cycle') }}</span><strong>{{ contract.billingCycle }}</strong></div>
          <div><span>{{ t('cd.billDay') }}</span><strong>{{ contract.billDay }}</strong></div>
        </div>
      </div>

      <div class="panel">
        <div class="row tab-bar">
          <button v-for="t in tabs" :key="t.key" class="sm" :class="{ primary: tab === t.key }" @click="switchTab(t.key)">{{ t.label }}</button>
        </div>

        <div v-if="tab === 'overview'" class="tab-body">
          <div class="kv-grid">
            <div><span>{{ t('cd.contractNo') }}</span><strong>{{ contract.contractNo }}</strong></div>
            <div><span>{{ t('cd.status') }}</span><strong>{{ contractStatusLabel(contract.contractStatus) }}</strong></div>
            <div><span>{{ t('cd.tenant') }}</span><a v-if="contract.personId" @click="openPerson(contract.personId)">{{ contract.personName }} →</a><span v-else>—</span></div>
            <div><span>{{ t('cd.house') }}</span><a v-if="contract.houseId" @click="openHouse(contract.houseId)">{{ contract.houseName }} →</a><span v-else>—</span></div>
            <div><span>{{ t('cd.start') }}</span><strong>{{ contract.startDate }}</strong></div>
            <div><span>{{ t('cd.end') }}</span><strong>{{ contract.endDate }}</strong></div>
            <div><span>{{ t('cd.monthlyRent') }}</span><strong>{{ money(contract.rentAmount) }}</strong></div>
            <div><span>{{ t('cd.depositAmount') }}</span><strong>{{ money(contract.depositAmount) }}</strong></div>
            <div><span>{{ t('cd.cycle') }}</span><strong>{{ contract.billingCycle }}</strong></div>
            <div><span>{{ t('cd.billDay') }}</span><strong>{{ contract.billDay }}</strong></div>
          </div>
        </div>

        <div v-else-if="tab === 'persons'" class="tab-body">
          <div class="section-title">{{ t('cd.tenant') }}</div>
          <div class="entity-row"><strong>{{ contract.personName }}</strong><button class="sm" @click="openPerson(contract.personId)">{{ t('cd.openPerson') }}</button></div>
          <div class="section-title">{{ t('cd.cohabitants', { n: cohabitants.length }) }}</div>
          <div class="row" style="margin-bottom:10px;flex-wrap:wrap">
            <div class="field" style="flex:2;min-width:180px"><label>{{ t('cd.persons') }}</label><SearchSelect v-model="cohabForm.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" :placeholder="t('cd.searchPerson')" /></div>
            <div class="field"><label>{{ t('cd.relation') }}</label><select v-model="cohabForm.relationType"><option value="SPOUSE">{{ t('cd.spouse') }}</option><option value="CHILD">{{ t('cd.child') }}</option><option value="PARENT">{{ t('cd.parent') }}</option><option value="FAMILY">{{ t('cd.family') }}</option><option value="OTHER">{{ t('cd.other') }}</option></select></div>
            <div class="field"><label>{{ t('cd.startShort') }}</label><input v-model="cohabForm.startDate" type="date" /></div>
            <div class="field"><label>{{ t('cd.endShort') }}</label><input v-model="cohabForm.endDate" type="date" /></div>
            <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addCohabitant">{{ t('cd.addCohabitant') }}</button></div>
          </div>
          <div v-if="!cohabitants.length" class="empty">{{ t('cd.noCohabitants') }}</div>
          <div v-for="c in cohabitants" :key="c.id" class="entity-row"><div><strong>{{ c.personName }}</strong><span class="small muted"> · {{ relationLabel(c.relationType) }} · {{ c.startDate || '' }} ~ {{ c.endDate || t('cd.longTerm') }}</span></div><div class="row"><span class="badge green">{{ relationStatusLabel(c.cohabitantStatus) }}</span><button class="sm danger" :disabled="busy" @click="removeCohabitant(c)">{{ t('cd.remove') }}</button></div></div>
        </div>

        <div v-else-if="tab === 'house'" class="tab-body">
          <div class="entity-row"><div><strong>{{ contract.houseName }}</strong><div class="small muted">{{ t('cd.houseId') }}: {{ contract.houseId }}</div></div><button class="sm" @click="openHouse(contract.houseId)">{{ t('cd.openHouse') }}</button></div>
        </div>

        <div v-else-if="tab === 'bills'" class="tab-body">
          <div v-if="!bills.length" class="empty">{{ t('cd.noBills') }}</div>
          <div v-else class="table-wrap"><table><thead><tr><th>{{ t('cd.billNo') }}</th><th>{{ t('cd.period') }}</th><th>{{ t('cd.payable') }}</th><th>{{ t('cd.paid') }}</th><th>{{ t('cd.status') }}</th></tr></thead><tbody><tr v-for="b in bills" :key="b.id"><td class="mono">{{ b.billNo }}</td><td>{{ b.periodStart }} ~ {{ b.periodEnd }}</td><td>{{ money(b.payableAmount) }}</td><td>{{ money(b.paidAmount) }}</td><td><span class="badge" :class="b.billStatus === 'PAID' ? 'green' : 'orange'">{{ b.billStatus }}</span></td></tr></tbody></table></div>
        </div>

        <div v-else-if="tab === 'deposit'" class="tab-body">
          <div v-if="deposit" class="kv-grid"><div><span>{{ t('cd.depositLabel') }}</span><strong>{{ money(deposit.amount) }}</strong></div><div><span>{{ t('cd.refunded') }}</span><strong>{{ money(deposit.refundedAmount) }}</strong></div><div><span>{{ t('cd.status') }}</span><strong>{{ deposit.depositStatus }}</strong></div></div>
          <div v-else class="empty">{{ t('cd.noDeposit') }}</div>
          <div class="section-title">{{ t('cd.subsidies', { n: subsidies.length }) }}</div>
          <div v-if="!subsidies.length" class="empty">{{ t('cd.noSubsidy') }}</div>
          <div v-for="s in subsidies" :key="s.id" class="entity-row"><span>{{ s.subsidyType }} · {{ money(s.amount) }}</span><span class="badge">{{ s.subsidyStatus }}</span></div>
        </div>

        <div v-else-if="tab === 'files'" class="tab-body">
          <div class="row" style="margin-bottom:10px"><input type="file" :disabled="fileBusy" @change="uploadFile" /><span v-if="fileBusy" class="small muted">{{ t('cd.uploading') }}</span></div>
          <div v-if="!files.length" class="empty">{{ t('cd.noFiles') }}</div>
          <div v-for="f in files" :key="f.id" class="entity-row"><div>{{ f.fileName }}<div class="small muted">{{ f.fileSize }} bytes · {{ f.createTime }}</div></div><button class="sm" @click="api.downloadFile(f.id, f.fileName)">{{ t('cd.download') }}</button></div>
        </div>

        <div v-else-if="tab === 'relations'" class="tab-body">
          <EntityDetailTabs type="CONTRACT" :entity-id="contract.id" />
        </div>
        <div v-else-if="tab === 'changes'" class="tab-body">
          <div v-if="!changes.length" class="empty">{{ t('cd.noChanges') }}</div>
          <div v-for="c in changes" :key="c.id" class="entity-row"><div><strong>{{ c.changeType }}</strong><div class="small muted">{{ c.changeReason || c.reason || '' }}</div></div><span class="badge">{{ c.changeStatus || c.status }}</span></div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.contract-head .summary { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:10px; }
.contract-head .summary div { background:var(--bg); border:1px solid var(--line); border-radius:6px; padding:10px; display:flex; flex-direction:column; gap:3px; }
.contract-head .summary span { font-size:11px; color:var(--muted); }
.contract-head .summary strong { font-size:15px; }
.tab-bar { gap:6px; flex-wrap:wrap; border-bottom:1px solid var(--line); padding-bottom:8px; }
.tab-count { margin-left:5px; font-size:10px; opacity:.75; }
.tab-body { padding-top:12px; }
.kv-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; }
.kv-grid > div { border:1px solid var(--line); border-radius:6px; padding:10px; display:flex; flex-direction:column; gap:4px; }
.kv-grid span { font-size:11px; color:var(--muted); }
.kv-grid strong { font-size:14px; }
.kv-grid a { color:var(--brand); cursor:pointer; }
.section-title { font-weight:600; margin:14px 0 8px; }
.entity-row { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:10px 0; border-bottom:1px solid var(--line); }
@media (max-width:800px) { .contract-head .summary { grid-template-columns:repeat(2,1fr); } }
</style>
