<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { api } from '../api'

const project = ref(null)
const contracts = ref([])
const selectedContractId = ref('')
const changes = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ changeType: 'RENT_CHANGE', rentAmount: 1500, endDate: '2027-10-31', effectiveDate: '2026-12-01', reason: '页面调整' })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red', APPROVING: 'orange' }[s] || '')

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
    if (!selectedContractId.value && contracts.value.length) selectedContractId.value = contracts.value[0].id
    await loadChanges()
  } catch (e) { error.value = e.message }
}

async function loadChanges() {
  if (!selectedContractId.value) return
  changes.value = await api.changes(selectedContractId.value)
}

async function create() {
  busy.value = true; error.value = ''
  try {
    await api.createChange(selectedContractId.value, {
      changeType: form.changeType,
      after: form.changeType === 'RENT_CHANGE' ? { rentAmount: Number(form.rentAmount) } : { endDate: form.endDate },
      effectiveDate: form.effectiveDate,
      reason: form.reason
    })
    await loadChanges()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function submit(id) { await run(() => api.submitChange(id)) }
async function approve(id) { await run(() => api.approveChange(id, { approverName: '经理B', comment: '通过' })) }
async function reject(id) { await run(() => api.rejectChange(id, { approverName: '经理B', comment: '驳回' })) }

async function run(fn) {
  busy.value = true; error.value = ''
  try { await fn(); await loadChanges() } catch (e) { error.value = e.message } finally { busy.value = false }
}

watch(selectedContractId, loadChanges)
onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>合同变更</h2><p>{{ project.orgName }} · 租金/期限/换房/退租</p></div>
          <select v-model="selectedContractId" style="max-width:320px">
            <option value="">选择合同</option>
            <option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.contractNo }} · {{ c.personName }}</option>
          </select>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>新建变更</h2><span class="small muted">提交后进入平台审批</span></div>
        <div class="row">
          <div class="field"><label>类型</label>
            <select v-model="form.changeType"><option value="RENT_CHANGE">租金变更</option><option value="TERM_CHANGE">期限变更</option><option value="TERMINATION">退租</option></select>
          </div>
          <div class="field" v-if="form.changeType === 'RENT_CHANGE'"><label>新租金</label><input v-model.number="form.rentAmount" type="number" /></div>
          <div class="field" v-else><label>新结束日期</label><input v-model="form.endDate" type="date" /></div>
          <div class="field"><label>生效日期</label><input v-model="form.effectiveDate" type="date" /></div>
          <div class="field"><label>原因</label><input v-model="form.reason" /></div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">创建变更</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>变更记录</h2><span class="small muted">{{ changes.length }} 条</span></div>
        <div v-if="!changes.length" class="empty">暂无变更</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>类型</th><th>生效日期</th><th>状态</th><th>原因</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="c in changes" :key="c.id">
                <td>{{ c.changeType }}</td><td>{{ c.effectiveDate }}</td>
                <td><span class="badge" :class="statusClass(c.changeStatus)">{{ c.changeStatus }}</span></td>
                <td>{{ c.reason }}</td>
                <td class="row">
                  <button class="sm" v-if="c.changeStatus === 'DRAFT'" @click="submit(c.id)">提交</button>
                  <button class="sm" v-if="c.changeStatus === 'APPROVING'" @click="approve(c.id)">通过</button>
                  <button class="sm danger" v-if="c.changeStatus === 'APPROVING'" @click="reject(c.id)">驳回</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>
