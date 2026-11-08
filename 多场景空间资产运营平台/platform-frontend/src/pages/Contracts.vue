<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const contracts = ref([])
const persons = ref([])
const houses = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({
  contractNo: '', houseId: '', personId: '', startDate: '2026-11-01', endDate: '2027-10-31',
  rentAmount: 1200, depositAmount: 1200
})
const billForm = reactive({ contractId: '', periodStart: '2026-11-01', periodEnd: '2026-11-30', amount: 1200 })

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  if (chosen) return chosen
  return all.slice().sort((a, b) =>
    ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
    ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
  )[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    localStorage.setItem('platformProjectId', project.value.id)
    const [c, p, h] = await Promise.all([
      api.contracts(project.value.id), api.persons(), api.houses(project.value.id)
    ])
    contracts.value = c; persons.value = p; houses.value = h
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
    if (!billForm.contractId && c.length) billForm.contractId = c[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.contractNo.trim()) throw new Error('请填写合同编号')
    await api.createContract({
      projectId: project.value.id, contractNo: form.contractNo.trim(),
      houseId: form.houseId, personId: form.personId,
      startDate: form.startDate, endDate: form.endDate,
      rentAmount: Number(form.rentAmount), depositAmount: Number(form.depositAmount),
      billingCycle: 'MONTH', billDay: 1
    })
    form.contractNo = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function generateBill() {
  busy.value = true; error.value = ''
  try {
    if (!billForm.contractId) throw new Error('请选择合同')
    await api.generateBill(billForm.contractId, {
      periodStart: billForm.periodStart, periodEnd: billForm.periodEnd,
      amount: Number(billForm.amount)
    })
    error.value = ''
    alert('账单已生成，请到“收费与账务”查看')
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>保障房合同</h2><p>{{ project.orgName }} · 合同创建与账单生成</p></div><span class="pill">CONTRACT</span></div>
        <div class="row">
          <div class="field"><label>合同编号</label><input v-model="form.contractNo" placeholder="如 HT2026001" /></div>
          <div class="field"><label>房屋</label>
            <select v-model="form.houseId"><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select>
          </div>
          <div class="field"><label>承租人</label>
            <select v-model="form.personId"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select>
          </div>
          <div class="field"><label>开始日期</label><input v-model="form.startDate" type="date" /></div>
          <div class="field"><label>结束日期</label><input v-model="form.endDate" type="date" /></div>
          <div class="field"><label>月租金</label><input v-model.number="form.rentAmount" type="number" /></div>
          <div class="field"><label>押金</label><input v-model.number="form.depositAmount" type="number" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">创建合同</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>合同列表</h2><span class="small muted">生效合同可生成租金账单</span></div>
        <div v-if="!contracts.length" class="empty">暂无合同</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>合同编号</th><th>房屋</th><th>承租人</th><th>租金</th><th>押金</th><th>状态</th></tr></thead>
            <tbody>
              <tr v-for="c in contracts" :key="c.id">
                <td class="mono">{{ c.contractNo }}</td><td>{{ c.houseName }}</td><td>{{ c.personName }}</td>
                <td>¥{{ money(c.rentAmount) }}</td><td>¥{{ money(c.depositAmount) }}</td>
                <td><span class="badge" :class="c.contractStatus === 'ACTIVE' ? 'green' : 'orange'">{{ c.contractStatus }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>生成租金账单</h2><span class="small muted">补贴会在账单生成时自动抵扣</span></div>
        <div class="row">
          <div class="field"><label>合同</label>
            <select v-model="billForm.contractId"><option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.contractNo }}</option></select>
          </div>
          <div class="field"><label>周期开始</label><input v-model="billForm.periodStart" type="date" /></div>
          <div class="field"><label>周期结束</label><input v-model="billForm.periodEnd" type="date" /></div>
          <div class="field"><label>金额</label><input v-model.number="billForm.amount" type="number" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button :disabled="busy" @click="generateBill">生成账单</button></div>
        </div>
      </div>
    </template>
  </div>
</template>
