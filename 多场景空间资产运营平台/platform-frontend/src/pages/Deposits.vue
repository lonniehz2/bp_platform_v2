<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const project = ref(null)
const route = useRoute()
const router = useRouter()
const contracts = ref([])
const selectedContractId = ref('')
const deposit = ref(null)
const subsidies = ref([])
const error = ref('')
const busy = ref(false)
const payForm = reactive({ amount: '', operatorName: '收费员A' })
const refundForm = reactive({ amount: '', operatorName: '收费员A', reason: '退租退押' })
const subsidyForm = reactive({ subsidyType: 'RENT_SUBSIDY', amount: 300, startDate: '2026-11-01', endDate: '2026-11-30' })

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  return chosen || all.slice().sort((a, b) =>
    ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
    ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
  )[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    contracts.value = await api.contracts(project.value.id)
    const requested = String(route.query.contractId || '')
    if (requested && contracts.value.some(c => String(c.id) === requested)) selectedContractId.value = requested
    else if (!selectedContractId.value && contracts.value.length) selectedContractId.value = contracts.value[0].id
    await loadContract()
  } catch (e) { error.value = e.message }
}

async function loadContract() {
  deposit.value = null; subsidies.value = []
  if (!selectedContractId.value) return
  try {
    const [d, s] = await Promise.all([api.deposit(selectedContractId.value), api.subsidies(selectedContractId.value)])
    deposit.value = d; subsidies.value = s
    payForm.amount = Number(d.amount) - Number(d.paidAmount)
    refundForm.amount = Number(d.paidAmount) - Number(d.refundedAmount)
  } catch (e) {
    if (!String(e.message).includes('不存在')) error.value = e.message
  }
}

async function pay() {
  busy.value = true; error.value = ''
  try {
    await api.payDeposit(selectedContractId.value, {
      amount: Number(payForm.amount), operatorName: payForm.operatorName, remark: '收取押金'
    })
    await loadContract()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function refund() {
  busy.value = true; error.value = ''
  try {
    await api.refundDeposit(deposit.value.id, {
      amount: Number(refundForm.amount), operatorName: refundForm.operatorName, reason: refundForm.reason
    })
    await loadContract()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function addSubsidy() {
  busy.value = true; error.value = ''
  try {
    await api.createSubsidy(selectedContractId.value, {
      subsidyType: subsidyForm.subsidyType, amount: Number(subsidyForm.amount),
      startDate: subsidyForm.startDate, endDate: subsidyForm.endDate, remark: '页面新增补贴'
    })
    await loadContract()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

watch(selectedContractId, loadContract)
onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="route.query.contractId" class="alert">来自合同 {{ route.query.contractId }} 的押金/补贴 <button class="sm" @click="router.replace('/guarantee/deposits')">清除合同筛选</button></div>
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>押金与补贴</h2><p>{{ project.orgName }} · 按合同管理押金和租金补贴</p></div>
          <select v-model="selectedContractId" style="max-width:320px">
            <option value="">选择合同</option>
            <option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.contractNo }} · {{ c.personName }}</option>
          </select>
        </div>
      </div>

      <div class="grid" style="grid-template-columns: 1fr 1fr">
        <div class="panel">
          <div class="panel-head"><h2>押金</h2><span class="badge" :class="deposit?.depositStatus === 'HELD' ? 'green' : 'orange'">{{ deposit?.depositStatus || '无' }}</span></div>
          <div v-if="!deposit" class="empty">暂无押金记录</div>
          <template v-else>
            <div class="row" style="margin-bottom:12px">
              <div class="field"><label>应收</label><div>¥{{ money(deposit.amount) }}</div></div>
              <div class="field"><label>已收</label><div>¥{{ money(deposit.paidAmount) }}</div></div>
              <div class="field"><label>已退</label><div>¥{{ money(deposit.refundedAmount) }}</div></div>
            </div>
            <div class="row" style="margin-bottom:8px">
              <div class="field"><label>收取金额</label><input v-model.number="payForm.amount" type="number" /></div>
              <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="pay">收取押金</button></div>
            </div>
            <div class="row">
              <div class="field"><label>退还金额</label><input v-model.number="refundForm.amount" type="number" /></div>
              <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button :disabled="busy" @click="refund">退还押金</button></div>
            </div>
            <div class="small muted" style="margin-top:10px">流水 {{ deposit.transactions?.length || 0 }} 条</div>
          </template>
        </div>

        <div class="panel">
          <div class="panel-head"><h2>租金补贴</h2><span class="small muted">{{ subsidies.length }} 条</span></div>
          <div class="row" style="margin-bottom:10px">
            <div class="field"><label>金额/月</label><input v-model.number="subsidyForm.amount" type="number" /></div>
            <div class="field"><label>开始</label><input v-model="subsidyForm.startDate" type="date" /></div>
            <div class="field"><label>结束</label><input v-model="subsidyForm.endDate" type="date" /></div>
            <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="addSubsidy">新增补贴</button></div>
          </div>
          <div v-if="!subsidies.length" class="empty">暂无补贴</div>
          <div class="table-wrap" v-else>
            <table><thead><tr><th>类型</th><th>金额</th><th>期间</th><th>状态</th></tr></thead>
              <tbody><tr v-for="s in subsidies" :key="s.id"><td>{{ s.subsidyType }}</td><td>¥{{ money(s.subsidyAmount) }}</td><td class="small">{{ s.startDate }} ~ {{ s.endDate }}</td><td><span class="badge green">{{ s.subsidyStatus }}</span></td></tr></tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
