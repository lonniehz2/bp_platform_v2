<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { can } from '../permissions'

const route = useRoute()
const router = useRouter()
const contract = ref(null)
const error = ref('')
const busy = ref(false)
const tab = ref(String(route.query.tab || 'overview'))
const cohabitants = ref([])
const bills = ref([])
const deposit = ref(null)
const subsidies = ref([])
const files = ref([])
const changes = ref([])
const loaded = ref({})

const tabs = computed(() => [
  { key: 'overview', label: '概览' },
  { key: 'persons', label: '人员', count: cohabitants.value.length },
  { key: 'house', label: '房屋' },
  can('billing') ? { key: 'bills', label: '账单与收款', count: bills.value.length } : null,
  can('deposits') ? { key: 'deposit', label: '押金/补贴', count: subsidies.value.length } : null,
  { key: 'files', label: '附件', count: files.value.length },
  { key: 'changes', label: '变更记录', count: changes.value.length }
].filter(Boolean))

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function load() {
  error.value = ''
  try {
    const projects = await api.projects()
    const saved = localStorage.getItem('platformProjectId')
    const ordered = [
      ...projects.filter(p => String(p.id) === String(saved)),
      ...projects.filter(p => String(p.id) !== String(saved))
    ]
    for (const project of ordered) {
      const list = await api.contracts(project.id)
      const found = list.find(c => String(c.id) === String(route.params.id))
      if (found) { contract.value = found; break }
    }
    if (!contract.value) throw new Error('合同不存在或不在当前项目')
    await loadTab()
  } catch (e) { error.value = e.message }
}

async function loadTab() {
  if (!contract.value) return
  const key = tab.value
  if (loaded.value[key]) return
  try {
    if (key === 'persons') cohabitants.value = await api.cohabitants(contract.value.id)
    if (key === 'bills') bills.value = await api.contractBills(contract.value.id)
    if (key === 'deposit') { deposit.value = await api.deposit(contract.value.id); subsidies.value = await api.subsidies(contract.value.id) }
    if (key === 'files') files.value = await api.files('CONTRACT', contract.value.id)
    if (key === 'changes') changes.value = await api.changes(contract.value.id)
    loaded.value[key] = true
  } catch (e) { error.value = e.message }
}

function switchTab(key) {
  tab.value = key
  router.replace({ query: { ...route.query, tab: key } })
}

function openPerson(id) { if (id) router.push(`/guarantee/persons?id=${id}`) }
function openHouse(id) { if (id) router.push(`/guarantee/houses?id=${id}`) }

onMounted(load)
watch(() => route.params.id, load)
watch(tab, loadTab)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!contract" class="panel"><div class="empty">加载合同…</div></div>
    <template v-else>
      <div class="panel contract-head">
        <div class="panel-head">
          <div>
            <h2>{{ contract.contractNo }}</h2>
            <p>{{ contract.personName }} · {{ contract.houseName }} · {{ contract.startDate }} ~ {{ contract.endDate }}</p>
          </div>
          <div class="row"><span class="badge" :class="contract.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ contract.contractStatus }}</span><button class="sm" @click="router.push('/guarantee/contracts')">返回列表</button></div>
        </div>
        <div class="summary">
          <div><span>租金</span><strong>{{ money(contract.rentAmount) }}</strong></div>
          <div><span>押金</span><strong>{{ money(contract.depositAmount) }}</strong></div>
          <div><span>账单周期</span><strong>{{ contract.billingCycle }}</strong></div>
          <div><span>账单日</span><strong>{{ contract.billDay }}</strong></div>
        </div>
      </div>

      <div class="panel">
        <div class="row tab-bar">
          <button v-for="t in tabs" :key="t.key" class="sm" :class="{ primary: tab === t.key }" @click="switchTab(t.key)">{{ t.label }}<span v-if="t.count !== undefined" class="tab-count">{{ t.count }}</span></button>
        </div>

        <div v-if="tab === 'overview'" class="tab-body">
          <div class="kv-grid">
            <div><span>合同编号</span><strong>{{ contract.contractNo }}</strong></div>
            <div><span>状态</span><strong>{{ contract.contractStatus }}</strong></div>
            <div><span>承租人</span><a v-if="contract.personId" @click="openPerson(contract.personId)">{{ contract.personName }} →</a><span v-else>—</span></div>
            <div><span>房屋</span><a v-if="contract.houseId" @click="openHouse(contract.houseId)">{{ contract.houseName }} →</a><span v-else>—</span></div>
            <div><span>开始日期</span><strong>{{ contract.startDate }}</strong></div>
            <div><span>结束日期</span><strong>{{ contract.endDate }}</strong></div>
            <div><span>月租金</span><strong>{{ money(contract.rentAmount) }}</strong></div>
            <div><span>押金</span><strong>{{ money(contract.depositAmount) }}</strong></div>
            <div><span>账单周期</span><strong>{{ contract.billingCycle }}</strong></div>
            <div><span>账单日</span><strong>{{ contract.billDay }}</strong></div>
          </div>
        </div>

        <div v-else-if="tab === 'persons'" class="tab-body">
          <div class="section-title">承租人</div>
          <div class="entity-row"><strong>{{ contract.personName }}</strong><button class="sm" @click="openPerson(contract.personId)">打开人员</button></div>
          <div class="section-title">同住人（{{ cohabitants.length }}）</div>
          <div v-if="!cohabitants.length" class="empty">暂无同住人</div>
          <div v-for="c in cohabitants" :key="c.id" class="entity-row"><div><strong>{{ c.personName }}</strong><span class="small muted"> · {{ c.relationType }} · {{ c.startDate || '' }} ~ {{ c.endDate || '长期' }}</span></div><span class="badge green">{{ c.cohabitantStatus }}</span></div>
        </div>

        <div v-else-if="tab === 'house'" class="tab-body">
          <div class="entity-row"><div><strong>{{ contract.houseName }}</strong><div class="small muted">房屋 ID：{{ contract.houseId }}</div></div><button class="sm" @click="openHouse(contract.houseId)">打开房源</button></div>
        </div>

        <div v-else-if="tab === 'bills'" class="tab-body">
          <div v-if="!bills.length" class="empty">暂无账单</div>
          <div v-else class="table-wrap"><table><thead><tr><th>账单号</th><th>账期</th><th>应付</th><th>已收</th><th>状态</th></tr></thead><tbody><tr v-for="b in bills" :key="b.id"><td class="mono">{{ b.billNo }}</td><td>{{ b.periodStart }} ~ {{ b.periodEnd }}</td><td>{{ money(b.payableAmount) }}</td><td>{{ money(b.paidAmount) }}</td><td><span class="badge" :class="b.billStatus === 'PAID' ? 'green' : 'orange'">{{ b.billStatus }}</span></td></tr></tbody></table></div>
        </div>

        <div v-else-if="tab === 'deposit'" class="tab-body">
          <div v-if="deposit" class="kv-grid"><div><span>押金金额</span><strong>{{ money(deposit.amount) }}</strong></div><div><span>已退</span><strong>{{ money(deposit.refundedAmount) }}</strong></div><div><span>状态</span><strong>{{ deposit.depositStatus }}</strong></div></div>
          <div v-else class="empty">暂无押金记录</div>
          <div class="section-title">补贴（{{ subsidies.length }}）</div>
          <div v-if="!subsidies.length" class="empty">暂无补贴</div>
          <div v-for="s in subsidies" :key="s.id" class="entity-row"><span>{{ s.subsidyType }} · {{ money(s.amount) }}</span><span class="badge">{{ s.subsidyStatus }}</span></div>
        </div>

        <div v-else-if="tab === 'files'" class="tab-body">
          <div v-if="!files.length" class="empty">暂无附件</div>
          <div v-for="f in files" :key="f.id" class="entity-row"><div>{{ f.fileName }}<div class="small muted">{{ f.fileSize }} bytes · {{ f.createTime }}</div></div><button class="sm" @click="api.downloadFile(f.id, f.fileName)">下载</button></div>
        </div>

        <div v-else-if="tab === 'changes'" class="tab-body">
          <div v-if="!changes.length" class="empty">暂无变更记录</div>
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
