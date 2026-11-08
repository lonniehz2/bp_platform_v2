<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

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
  const rows = [['合同编号', '承租人', '房屋', '开始日期', '结束日期', '月租金', '状态']]
  filteredContracts.value.forEach(c => rows.push([c.contractNo, c.personName || '', c.houseName || '', c.startDate, c.endDate, c.rentAmount, c.contractStatus]))
  const csv = '\ufeff' + rows.map(r => r.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `监管报送_${project.value?.orgCode || 'report'}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>监管报送</h2><p>{{ project?.orgName || '未选择项目' }} · 合同、人员、账单汇总导出</p></div><button class="primary" @click="exportCsv">导出报送 CSV</button></div>
      <div class="row" style="margin-bottom:12px">
        <div class="field"><label>开始日期</label><input v-model="from" type="date" /></div>
        <div class="field"><label>结束日期</label><input v-model="to" type="date" /></div>
      </div>
      <div class="grid cards">
        <div class="card"><div class="label">合同数</div><div class="value">{{ filteredContracts.length }}</div><div class="hint">生效 {{ activeContracts }}</div></div>
        <div class="card"><div class="label">月租金合计</div><div class="value">¥{{ totalRent.toLocaleString('zh-CN') }}</div><div class="hint">按合同月租金</div></div>
        <div class="card"><div class="label">人员数</div><div class="value">{{ persons.length }}</div><div class="hint">人员档案</div></div>
        <div class="card"><div class="label">账单金额</div><div class="value">¥{{ totalBills.toLocaleString('zh-CN') }}</div><div class="hint">按账期筛选</div></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>合同明细</h2><span class="small muted">{{ from || '不限' }} ~ {{ to || '不限' }}</span></div>
      <div v-if="!filteredContracts.length" class="empty">暂无数据</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>合同编号</th><th>承租人</th><th>房屋</th><th>开始</th><th>结束</th><th>月租金</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="c in filteredContracts" :key="c.id">
              <td class="mono">{{ c.contractNo }}</td><td>{{ c.personName }}</td><td>{{ c.houseName }}</td>
              <td class="small">{{ c.startDate }}</td><td class="small">{{ c.endDate }}</td>
              <td>¥{{ Number(c.rentAmount || 0).toFixed(2) }}</td><td>{{ c.contractStatus }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
