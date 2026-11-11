<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const bills = ref([])
const contracts = ref([])
const houses = ref([])
const alerts = ref([])
const error = ref('')
const busy = ref(false)
const lastRun = ref('')

const today = new Date()
const tpl = (key, params) => t(key, params)
const dateKey = (d) => String(d).slice(0, 10)
const daysBetween = (a, b) => Math.ceil((new Date(b) - new Date(a)) / 86400000)

const findings = computed(() => {
  const out = []
  const overdue = bills.value.filter(b => b.billStatus === 'OVERDUE' || (b.billStatus !== 'PAID' && b.periodEnd && daysBetween(b.periodEnd, today) > 0))
  if (overdue.length) {
    const amount = overdue.reduce((s, b) => s + Math.max(0, Number(b.payableAmount || b.amount || 0) - Number(b.paidAmount || 0)), 0).toLocaleString('zh-CN')
    out.push({ key: 'OVERDUE', levelKey: 'high', title: t('patrol.overdueTitle', { n: overdue.length }), detail: t('patrol.overdueDetail', { amount }), suggestion: t('patrol.overdueSuggestion') })
  }
  const vacant = houses.value.filter(h => h.houseStatus === 'VACANT')
  if (vacant.length > 10) out.push({ key: 'VACANT', levelKey: 'medium', title: t('patrol.vacantTitle', { n: vacant.length }), detail: t('patrol.vacantDetail'), suggestion: t('patrol.vacantSuggestion') })
  const expiring = contracts.value.filter(c => c.contractStatus === 'ACTIVE' && c.endDate && daysBetween(today, c.endDate) >= 0 && daysBetween(today, c.endDate) <= 60)
  if (expiring.length) out.push({ key: 'EXPIRING', levelKey: 'medium', title: t('patrol.expiringTitle', { n: expiring.length }), detail: t('patrol.expiringDetail'), suggestion: t('patrol.expiringSuggestion') })
  const pending = alerts.value.filter(a => a.alertStatus === 'PENDING')
  if (pending.length) out.push({ key: 'ALERT', levelKey: 'low', title: t('patrol.alertTitle', { n: pending.length }), detail: t('patrol.alertDetail'), suggestion: t('patrol.alertSuggestion') })
  return out
})

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    const id = project.value.id
    const [b, c, h, a] = await Promise.all([api.bills(id), api.contracts(id), api.houses(id), api.alerts(id)])
    bills.value = b; contracts.value = c; houses.value = h; alerts.value = a
    lastRun.value = new Date().toLocaleString('zh-CN')
  } catch (e) { error.value = e.message }
}

async function runPatrol() {
  busy.value = true; error.value = ''
  try {
    for (const f of findings.value) {
      if (f.key === 'ALERT') continue
      await api.createAlert({
        projectId: project.value.id,
        alertType: f.key === 'OVERDUE' ? 'OVERDUE' : 'RISK',
        alertLevel: f.levelKey === 'high' ? 'HIGH' : 'NORMAL',
        title: t('patrol.autoTitle', { title: f.title }),
        content: f.detail
      })
    }
    lastRun.value = new Date().toLocaleString('zh-CN')
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('patrol.title') }}</h2><p>{{ project?.orgName || t('patrol.noProject') }} · {{ t('patrol.subtitle') }}</p></div>
        <div class="row"><span class="small muted">{{ t('patrol.lastRun') }} {{ lastRun || '-' }}</span><button class="primary" :disabled="busy" @click="runPatrol">{{ t('patrol.run') }}</button></div>
      </div>
      <div class="grid cards">
        <div class="card"><div class="label">{{ t('patrol.rules') }}</div><div class="value">4</div><div class="hint">{{ t('patrol.ruleHint') }}</div></div>
        <div class="card"><div class="label">{{ t('patrol.findings') }}</div><div class="value">{{ findings.length }}</div><div class="hint">{{ t('patrol.currentRules') }}</div></div>
        <div class="card"><div class="label">{{ t('patrol.pendingAlerts') }}</div><div class="value">{{ alerts.filter(a => a.alertStatus === 'PENDING').length }}</div><div class="hint">{{ t('patrol.open') }}</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('patrol.results') }}</h2><span class="small muted">{{ t('patrol.resultsHint') }}</span></div>
      <div v-if="!findings.length" class="empty">{{ t('patrol.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('patrol.level') }}</th><th>{{ t('patrol.problem') }}</th><th>{{ t('patrol.detail') }}</th><th>{{ t('patrol.suggestion') }}</th></tr></thead>
          <tbody>
            <tr v-for="f in findings" :key="f.key">
              <td><span class="badge" :class="f.levelKey === 'high' ? 'red' : f.levelKey === 'medium' ? 'orange' : 'blue'">{{ t('patrol.'+f.levelKey) }}</span></td>
              <td>{{ f.title }}</td><td>{{ f.detail }}</td><td>{{ f.suggestion }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
