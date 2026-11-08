<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const persons = ref([])
const records = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ personId: '', creditType: 'VIOLATION', scoreChange: -5, reason: '', effectiveDate: '', expireDate: '' })
const typeName = (t) => ({ VIOLATION: '违规', ARREARS: '欠费', OTHER: '其他' }[t] || t)

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
    const [p, c] = await Promise.all([api.persons(), api.credits(project.value.id)])
    persons.value = p; records.value = c
    if (!form.personId && p.length) form.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.personId) throw new Error('请选择人员')
    await api.createCredit({
      projectId: project.value.id, personId: form.personId, creditType: form.creditType,
      scoreChange: Number(form.scoreChange || 0), reason: form.reason,
      effectiveDate: form.effectiveDate || null, expireDate: form.expireDate || null
    })
    form.reason = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function revoke(r) {
  busy.value = true; error.value = ''
  try { await api.revokeCredit(r.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>信用惩戒</h2><p>{{ project?.orgName || '未选择项目' }} · 违规、欠费、信用扣分</p></div><span class="badge blue">{{ records.length }} 条</span></div>
      <div class="row">
        <div class="field"><label>人员</label><select v-model="form.personId"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select></div>
        <div class="field"><label>类型</label><select v-model="form.creditType"><option value="VIOLATION">违规</option><option value="ARREARS">欠费</option><option value="OTHER">其他</option></select></div>
        <div class="field"><label>分值</label><input v-model.number="form.scoreChange" type="number" /></div>
        <div class="field" style="flex:2"><label>原因</label><input v-model="form.reason" /></div>
        <div class="field"><label>生效日期</label><input v-model="form.effectiveDate" type="date" /></div>
        <div class="field"><label>失效日期</label><input v-model="form.expireDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('credit')" class="primary" :disabled="busy" @click="create">新增记录</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>信用记录</h2><span class="small muted">有效 → 撤销</span></div>
      <div v-if="!records.length" class="empty">暂无信用记录</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>人员</th><th>类型</th><th>分值</th><th>原因</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ r.personName }}</td><td>{{ typeName(r.creditType) }}</td>
              <td><span :class="r.scoreChange < 0 ? 'badge red' : 'badge green'">{{ r.scoreChange }}</span></td>
              <td>{{ r.reason || '-' }}</td><td class="small">{{ r.effectiveDate || '-' }} ~ {{ r.expireDate || '-' }}</td>
              <td><span class="badge" :class="r.recordStatus === 'ACTIVE' ? 'orange' : 'blue'">{{ r.recordStatus }}</span></td>
              <td><button v-if="can('credit') && r.recordStatus === 'ACTIVE'" class="sm danger" @click="revoke(r)">撤销</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
