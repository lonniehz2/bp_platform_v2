<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import Pager from '../components/Pager.vue'

const project = ref(null)
const payments = ref([])
const page = ref(1)
const error = ref('')
const paged = computed(() => payments.value.slice((page.value - 1) * 10, page.value * 10))
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
      <div v-if="!payments.length" class="empty">暂无收款</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>收款单号</th><th>金额</th><th>方式</th><th>状态</th><th>收据</th><th>时间</th></tr></thead>
          <tbody>
            <tr v-for="p in paged" :key="p.id">
              <td class="mono">{{ p.paymentNo }}</td><td>¥{{ money(p.amount) }}</td>
              <td>{{ p.paymentMethod }}</td><td><span class="badge green">{{ p.paymentStatus }}</span></td>
              <td class="mono">{{ p.receiptNo || '-' }}</td><td class="small">{{ p.paidTime }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <Pager :total="payments.length" :page="page" @update:page="page = $event" />
    </div>
  </div>
</template>
