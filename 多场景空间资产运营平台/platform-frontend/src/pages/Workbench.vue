<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const applications = ref([])
const contracts = ref([])
const bills = ref([])
const workOrders = ref([])
const alerts = ref([])
const loading = ref(true)
const error = ref('')
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
  { label: '待处理工单', value: pendingWorkOrders.value.length, to: '/guarantee/work-orders' },
  { label: '未结清账单', value: unpaidBills.value.length, to: '/guarantee/billing' },
  { label: '待审申请', value: applications.value.filter(a => a.applicationStatus === 'SUBMITTED').length, to: '/guarantee/applications' }
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
      <div class="panel-head"><div><h2>我的工作台</h2><p>{{ project?.orgName || '未选择项目' }} · 今日待办和个人经营提醒</p></div><RouterLink to="/guarantee/cockpit">进入运营驾驶舱</RouterLink></div>
      <div class="grid cards">
        <div v-for="t in todos" :key="t.label" class="card"><div class="label">{{ t.label }}</div><div class="value">{{ t.value }}</div><RouterLink :to="t.to">去处理</RouterLink></div>
        <div class="card"><div class="label">风险提醒</div><div class="value">{{ activeAlerts }}</div><RouterLink to="/guarantee/alerts">查看预警</RouterLink></div>
        <div class="card"><div class="label">在租合同</div><div class="value">{{ contracts.filter(c => c.contractStatus === 'ACTIVE').length }}</div><RouterLink to="/guarantee/contracts">合同台账</RouterLink></div>
      </div>
    </div>
    <div class="grid two">
      <div class="panel"><div class="panel-head"><h2>最近合同</h2><RouterLink to="/guarantee/contracts">全部</RouterLink></div>
        <div v-if="!myContracts.length" class="empty">暂无合同</div>
        <div v-for="c in myContracts" :key="c.id" class="entity-row"><div><strong>{{ c.contractNo }}</strong><div class="small muted">{{ c.personName || '' }} · {{ c.houseName || '' }}</div></div><span class="badge green">{{ c.contractStatus }}</span></div>
      </div>
      <div class="panel"><div class="panel-head"><h2>待处理工单</h2><RouterLink to="/guarantee/work-orders">全部</RouterLink></div>
        <div v-if="!pendingWorkOrders.length" class="empty">暂无工单</div>
        <div v-for="w in pendingWorkOrders" :key="w.id" class="entity-row"><div><strong>{{ w.title }}</strong><div class="small muted">{{ w.orderNo }} · {{ w.assigneeName || '未分配' }}</div></div><span class="badge orange">{{ w.orderStatus }}</span></div>
      </div>
    </div>
    <div class="panel"><div class="panel-head"><h2>待收款提醒</h2><RouterLink to="/guarantee/billing">去收款</RouterLink></div>
      <div v-if="!unpaidBills.length" class="empty">暂无未结账单</div>
      <div v-for="b in unpaidBills" :key="b.id" class="entity-row"><div><strong>{{ b.billNo }}</strong><div class="small muted">{{ b.personName || '' }} · {{ b.periodStart }} ~ {{ b.periodEnd }}</div></div><span>¥{{ money(b.payableAmount || b.amount) }}</span></div>
    </div>
  </div>
</template>
