<script setup>
import { computed, onMounted, ref } from 'vue'
import { enumLabel } from '../enumLabels'
import { api } from '../api'
import DataTable from '../components/DataTable.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const project = ref(null)
const payments = ref([])
const page = ref(1)
const error = ref('')
const paged = computed(() => payments.value.slice((page.value - 1) * 10, page.value * 10))
const columns = [
  { key: 'paymentNo', title: t('cashflow.paymentNo'), width: '180px' },
  { key: 'amount', title: t('cashflow.amount'), width: '110px' },
  { key: 'paymentMethod', title: t('cashflow.method'), width: '100px' },
  { key: 'paymentStatus', title: t('cashflow.status'), width: '100px' },
  { key: 'receiptNo', title: t('cashflow.receipt'), width: '180px' },
  { key: 'paidTime', title: t('cashflow.time') }
]
const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
const total = computed(() => payments.value.reduce((sum, p) => sum + Number(p.amount || 0), 0))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) payments.value = await api.payments(project.value.id)
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid cards">
      <div class="card"><div class="label">{{ t('cashflow.count') }}</div><div class="value">{{ payments.length }}</div><div class="hint">{{ t('cashflow.currentProject') }}</div></div>
      <div class="card"><div class="label">{{ t('cashflow.total') }}</div><div class="value">¥{{ money(total) }}</div><div class="hint">{{ t('cashflow.all') }}</div></div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><div><h2>{{ t('cashflow.title') }}</h2><p>{{ project?.orgName || t('cashflow.noProject') }} · {{ t('cashflow.subtitle') }}</p></div></div>
      <DataTable :rows="paged" :columns="columns" :page="page" :page-size="10" :total="payments.length" @update:page="page = $event">
        <template #cell-amount="{ row }">¥{{ money(row.amount) }}</template>
        <template #cell-paymentStatus="{ row }"><span class="badge green">{{ enumLabel(row.paymentStatus) }}</span></template>
        <template #cell-paidTime="{ row }"><span class="small">{{ row.paidTime }}</span></template>
      </DataTable>

    </div>
  </div>
</template>
