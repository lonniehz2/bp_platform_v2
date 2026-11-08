<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const applications = ref([])
const contracts = ref([])
const bills = ref([])
const payments = ref([])
const devices = ref([])
const error = ref('')

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
const totalBills = computed(() => bills.value.reduce((s, b) => s + Number(b.amount || 0), 0))
const totalPaid = computed(() => bills.value.reduce((s, b) => s + Number(b.paidAmount || 0), 0))
const totalOutstanding = computed(() => bills.value.reduce((s, b) => s + Math.max(0, Number(b.payableAmount || b.amount || 0) - Number(b.paidAmount || 0)), 0))
const activeContracts = computed(() => contracts.value.filter(c => c.contractStatus === 'ACTIVE').length)

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
    const [a, c, b, p, d] = await Promise.all([
      api.applications(id), api.contracts(id), api.bills(id), api.payments(id), api.devices(id)
    ])
    applications.value = a; contracts.value = c; bills.value = b; payments.value = p; devices.value = d
  } catch (e) { error.value = e.message }
}

function exportBills() {
  const rows = [['账单号', '承租人', '周期开始', '周期结束', '账单金额', '补贴', '应付', '已收', '状态']]
  bills.value.forEach(b => rows.push([b.billNo, b.personName || '', b.periodStart, b.periodEnd, b.amount, b.discountAmount || 0, b.payableAmount || b.amount, b.paidAmount, b.billStatus]))
  const csv = '\ufeff' + rows.map(r => r.map(x => `"${String(x ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `保障房账单_${project.value?.orgCode || 'export'}.csv`
  link.click()
  URL.revokeObjectURL(link.href)
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>运营报表</h2><p>{{ project?.orgName || '未选择项目' }} · 申请、合同、账单、收款、设备</p></div><button class="primary" @click="exportBills">导出账单 CSV</button></div>
      <div class="grid cards">
        <div class="card"><div class="label">申请数</div><div class="value">{{ applications.length }}</div><div class="hint">待审 {{ applications.filter(a => a.applicationStatus === 'SUBMITTED').length }}</div></div>
        <div class="card"><div class="label">合同数</div><div class="value">{{ contracts.length }}</div><div class="hint">生效 {{ activeContracts }}</div></div>
        <div class="card"><div class="label">账单金额</div><div class="value">¥{{ money(totalBills) }}</div><div class="hint">已收 ¥{{ money(totalPaid) }}</div></div>
        <div class="card"><div class="label">欠费</div><div class="value">¥{{ money(totalOutstanding) }}</div><div class="hint">未结清 {{ bills.filter(b => b.billStatus !== 'PAID').length }} 笔</div></div>
        <div class="card"><div class="label">设备</div><div class="value">{{ devices.length }}</div><div class="hint">业务台账</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>账单状态分布</h2></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>状态</th><th>笔数</th><th>金额</th></tr></thead>
          <tbody>
            <tr v-for="s in ['UNPAID','PARTIAL','PAID','OVERDUE','WAIVED']" :key="s">
              <td><span class="badge" :class="s === 'PAID' ? 'green' : s === 'OVERDUE' ? 'red' : 'orange'">{{ s }}</span></td>
              <td>{{ bills.filter(b => b.billStatus === s).length }}</td>
              <td>¥{{ money(bills.filter(b => b.billStatus === s).reduce((sum, b) => sum + Number(b.amount || 0), 0)) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
