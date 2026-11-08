<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import Pager from '../components/Pager.vue'

const project = ref(null)
const bills = ref([])
const page = ref(1)
const error = ref('')

const unpaid = computed(() => bills.value.filter(b => b.billStatus !== 'PAID'))
const paged = computed(() => unpaid.value.slice((page.value - 1) * 10, page.value * 10))
const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
const outstanding = (b) => Math.max(0, Number(b.payableAmount || b.amount || 0) - Number(b.paidAmount || 0))
const totalOutstanding = computed(() => unpaid.value.reduce((sum, b) => sum + outstanding(b), 0))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) bills.value = await api.bills(project.value.id)
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="grid cards">
      <div class="card"><div class="label">未结清账单</div><div class="value">{{ unpaid.length }}</div><div class="hint">共 {{ bills.length }} 笔</div></div>
      <div class="card"><div class="label">欠费金额</div><div class="value">¥{{ money(totalOutstanding) }}</div><div class="hint">按应付减已收</div></div>
      <div class="card"><div class="label">逾期账单</div><div class="value">{{ unpaid.filter(b => b.billStatus === 'OVERDUE').length }}</div><div class="hint">状态 OVERDUE</div></div>
    </div>

    <div class="panel" style="margin-top:16px">
      <div class="panel-head"><div><h2>欠费清单</h2><p>{{ project?.orgName || '未选择项目' }} · 未结清账单</p></div><RouterLink to="/billing">去收款</RouterLink></div>
      <div v-if="!unpaid.length" class="empty">暂无欠费</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>账单号</th><th>承租人</th><th>周期</th><th>应付</th><th>已收</th><th>欠费</th><th>状态</th></tr></thead>
          <tbody>
            <tr v-for="b in paged" :key="b.id">
              <td class="mono">{{ b.billNo }}</td><td>{{ b.personName || '-' }}</td>
              <td class="small">{{ b.periodStart }} ~ {{ b.periodEnd }}</td>
              <td>¥{{ money(b.payableAmount || b.amount) }}</td><td>¥{{ money(b.paidAmount) }}</td>
              <td><strong>¥{{ money(outstanding(b)) }}</strong></td>
              <td><span class="badge" :class="b.billStatus === 'OVERDUE' ? 'red' : 'orange'">{{ b.billStatus }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pager :total="unpaid.length" :page="page" @update:page="page = $event" />
    </div>
  </div>
</template>
