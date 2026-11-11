<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'
import { sceneRoot } from '../scene'

const project = ref(null)
const applications = ref([])
const contracts = ref([])
const bills = ref([])
const workOrders = ref([])
const alerts = ref([])
const loading = ref(true)
const error = ref('')
const { t } = useI18n()
const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

const myContracts = computed(() => contracts.value.filter(c => c.contractStatus === 'ACTIVE').slice(0, 5))
const pendingWorkOrders = computed(() => workOrders.value.filter(w => w.orderStatus !== 'DONE' && w.orderStatus !== 'CLOSED').slice(0, 5))
const unpaidBills = computed(() => bills.value.filter(b => b.billStatus !== 'PAID').slice(0, 5))
const activeAlerts = computed(() => alerts.value.filter(a => a.alertStatus === 'PENDING').length)
const todos = computed(() => [
  { label: 'pendingWork', value: pendingWorkOrders.value.length, to: '/guarantee/work-orders' },
  { label: 'unpaid', value: unpaidBills.value.length, to: '/guarantee/billing' },
  { label: 'pendingApps', value: applications.value.filter(a => a.applicationStatus === 'SUBMITTED').length, to: '/guarantee/applications' }
])

async function load() {
  loading.value = true; error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const id = project.value.id
    const [a, c, b, w, al] = await Promise.all([api.applications(id), api.contracts(id), api.bills(id), api.workOrders(id), api.alerts(id)])
    applications.value = a; contracts.value = c; bills.value = b; workOrders.value = w; alerts.value = al
  } catch (e) { error.value = e.message } finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('workbench.title') }}</h2><p>{{ project?.orgName || t('common.project') }} · {{ t('workbench.subtitle') }}</p></div><RouterLink :to="sceneRoot() + '/cockpit'">{{ t('workbench.cockpit') }}</RouterLink></div>
      <div class="grid cards">
        <div v-for="item in todos" :key="item.label" class="card"><div class="label">{{ t(`workbench.${item.label}`) }}</div><div class="value">{{ item.value }}</div><RouterLink :to="item.to">{{ t('workbench.handle') }}</RouterLink></div>
        <div class="card"><div class="label">{{ t('workbench.alerts') }}</div><div class="value">{{ activeAlerts }}</div><RouterLink :to="sceneRoot() + '/alerts'">{{ t('workbench.viewAlerts') }}</RouterLink></div>
        <div class="card"><div class="label">{{ t('workbench.activeContracts') }}</div><div class="value">{{ contracts.filter(c => c.contractStatus === 'ACTIVE').length }}</div><RouterLink :to="sceneRoot() + '/contracts'">{{ t('workbench.contracts') }}</RouterLink></div>
      </div>
    </div>
    <div class="grid two">
      <div class="panel"><div class="panel-head"><h2>{{ t('workbench.recentContracts') }}</h2><RouterLink :to="sceneRoot() + '/contracts'">{{ t('workbench.all') }}</RouterLink></div>
        <div v-if="!myContracts.length" class="empty">{{ t('workbench.noContracts') }}</div>
        <div v-for="c in myContracts" :key="c.id" class="entity-row"><div><strong>{{ c.contractNo }}</strong><div class="small muted">{{ c.personName || '' }} · {{ c.houseName || '' }}</div></div><span class="badge green">{{ c.contractStatus }}</span></div>
      </div>
      <div class="panel"><div class="panel-head"><h2>{{ t('workbench.pendingOrders') }}</h2><RouterLink :to="sceneRoot() + '/work-orders'">{{ t('workbench.all') }}</RouterLink></div>
        <div v-if="!pendingWorkOrders.length" class="empty">{{ t('workbench.noOrders') }}</div>
        <div v-for="w in pendingWorkOrders" :key="w.id" class="entity-row"><div><strong>{{ w.title }}</strong><div class="small muted">{{ w.orderNo }} · {{ w.assigneeName || t('common.unassigned') }}</div></div><span class="badge orange">{{ w.orderStatus }}</span></div>
      </div>
    </div>
    <div class="panel"><div class="panel-head"><h2>{{ t('workbench.collection') }}</h2><RouterLink :to="sceneRoot() + '/billing'">{{ t('workbench.goCollect') }}</RouterLink></div>
      <div v-if="!unpaidBills.length" class="empty">{{ t('workbench.noUnpaid') }}</div>
      <div v-for="b in unpaidBills" :key="b.id" class="entity-row"><div><strong>{{ b.billNo }}</strong><div class="small muted">{{ b.personName || '' }} · {{ b.periodStart }} ~ {{ b.periodEnd }}</div></div><span>¥{{ money(b.payableAmount || b.amount) }}</span></div>
    </div>
  </div>
</template>
