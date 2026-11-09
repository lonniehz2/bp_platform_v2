<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import DataTable from '../components/DataTable.vue'

const project = ref(null)
const payments = ref([])
const page = ref(1)
const error = ref('')
const paged = computed(() => payments.value.slice((page.value - 1) * 10, page.value * 10))
const columns = [
  { key: 'paymentNo', title: '收款单号', width: '180px' },
  { key: 'amount', title: '金额', width: '110px' },
  { key: 'paymentMethod', title: '方式', width: '100px' },
  { key: 'paymentStatus', title: '状态', width: '100px' },
  { key: 'receiptNo', title: '收据', width: '180px' },
  { key: 'paidTime', title: '时间' }
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
      <div class="card"><div class="label">收款笔数</div><div class="value">{{ payments.length }}</div><div class="hint">当前项目</div></div>
      <div class="card"><div class="label">收款金额</div><div class="value">¥{{ money(total) }}</div><div class="hint">全部收款</div></div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><div><h2>资金流水</h2><p>{{ project?.orgName || '未选择项目' }} · 收款与收据</p></div></div>
      <DataTable :rows="paged" :columns="columns" :page="page" :page-size="10" :total="payments.length" @update:page="page = $event">
        <template #cell-amount="{ row }">¥{{ money(row.amount) }}</template>
        <template #cell-paymentStatus="{ row }"><span class="badge green">{{ row.paymentStatus }}</span></template>
        <template #cell-paidTime="{ row }"><span class="small">{{ row.paidTime }}</span></template>
      </DataTable>

    </div>
  </div>
</template>
