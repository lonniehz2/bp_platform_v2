<script setup>
import { computed, onMounted, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import { useI18n } from 'vue-i18n'
import { govReportHeader, govReportHeaderEn } from '../importTemplates'

const { t, locale } = useI18n()
const project = ref(null)
const contracts = ref([])
const persons = ref([])
const bills = ref([])
const from = ref('')
const to = ref('')
const error = ref('')

const filteredContracts = computed(() => contracts.value.filter(c => inRange(c.startDate)))
const activeContracts = computed(() => filteredContracts.value.filter(c => c.contractStatus === 'ACTIVE').length)
const totalRent = computed(() => filteredContracts.value.reduce((s, c) => s + Number(c.rentAmount || 0), 0))
const totalBills = computed(() => bills.value.filter(b => inRange(b.periodStart)).reduce((s, b) => s + Number(b.amount || 0), 0))

function inRange(date) {
  if (!date) return true
  const d = String(date).slice(0, 10)
  if (from.value && d < from.value) return false
  if (to.value && d > to.value) return false
  return true
}

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
    const [c, p, b] = await Promise.all([api.contracts(id), api.persons(), api.bills(id)])
    contracts.value = c; persons.value = p; bills.value = b
  } catch (e) { error.value = e.message }
}

function exportCsv() {
  const rows = [locale.value === 'en-US' ? govReportHeaderEn : govReportHeader]
  filteredContracts.value.forEach(c => rows.push([c.contractNo, c.personName || '', c.houseName || '', c.startDate, c.endDate, c.rentAmount, c.contractStatus]))
  const csv = '\ufeff' + rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${t('govReport.fileName')}_${project.value?.orgCode || 'report'}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('govReport.title') }}</h2><p>{{ project?.orgName || t('govReport.noProject') }} · {{ t('govReport.subtitle') }}</p></div><button class="primary" @click="exportCsv">{{ t('govReport.export') }}</button></div>
      <div class="row" style="margin-bottom:12px">
        <div class="field"><label>{{ t('govReport.from') }}</label><input v-model="from" type="date" /></div>
        <div class="field"><label>{{ t('govReport.to') }}</label><input v-model="to" type="date" /></div>
      </div>
      <div class="grid cards">
        <div class="card"><div class="label">{{ t('govReport.contracts') }}</div><div class="value">{{ filteredContracts.length }}</div><div class="hint">{{ t('govReport.active') }} {{ activeContracts }}</div></div>
        <div class="card"><div class="label">{{ t('govReport.rentTotal') }}</div><div class="value">¥{{ totalRent.toLocaleString('zh-CN') }}</div><div class="hint">{{ t('govReport.byRent') }}</div></div>
        <div class="card"><div class="label">{{ t('govReport.persons') }}</div><div class="value">{{ persons.length }}</div><div class="hint">{{ t('govReport.personHint') }}</div></div>
        <div class="card"><div class="label">{{ t('govReport.billTotal') }}</div><div class="value">¥{{ totalBills.toLocaleString('zh-CN') }}</div><div class="hint">{{ t('govReport.byPeriod') }}</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>{{ t('govReport.detail') }}</h2><span class="small muted">{{ from || t('govReport.unlimited') }} ~ {{ to || t('govReport.unlimited') }}</span></div>
      <div v-if="!filteredContracts.length" class="empty">{{ t('govReport.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('govReport.contractNo') }}</th><th>{{ t('govReport.tenant') }}</th><th>{{ t('govReport.house') }}</th><th>{{ t('govReport.start') }}</th><th>{{ t('govReport.end') }}</th><th>{{ t('govReport.rent') }}</th><th>{{ t('govReport.status') }}</th></tr></thead>
          <tbody>
            <tr v-for="c in filteredContracts" :key="c.id">
              <td class="mono">{{ c.contractNo }}</td><td>{{ c.personName }}</td><td>{{ c.houseName }}</td>
              <td class="small">{{ c.startDate }}</td><td class="small">{{ c.endDate }}</td>
              <td>¥{{ Number(c.rentAmount || 0).toFixed(2) }}</td><td>{{ enumLabel(c.contractStatus) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
