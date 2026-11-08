<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const houses = ref([])
const persons = ref([])
const records = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ visitorName: '', visitorPhone: '', purpose: '探访', houseId: '', personId: '', validStart: '', validEnd: '' })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red' }[s] || 'orange')

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
    const [h, p, r] = await Promise.all([api.houses(id), api.persons(), api.accessRecords(id)])
    houses.value = h; persons.value = p; records.value = r
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.visitorName.trim()) throw new Error('请填写访客姓名')
    await api.createAccessRecord({
      projectId: project.value.id, houseId: form.houseId || null, personId: form.personId || null,
      visitorName: form.visitorName.trim(), visitorPhone: form.visitorPhone, purpose: form.purpose,
      validStart: form.validStart || null, validEnd: form.validEnd || null
    })
    form.visitorName = ''; form.visitorPhone = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function approve(r, status) {
  busy.value = true; error.value = ''
  try {
    await api.approveAccessRecord(r.id, status)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>访客通行</h2><p>{{ project?.orgName || '未选择项目' }} · 访客登记与审批</p></div><span class="badge blue">{{ records.length }} 条</span></div>
      <div class="row">
        <div class="field"><label>访客姓名</label><input v-model="form.visitorName" /></div>
        <div class="field"><label>手机号</label><input v-model="form.visitorPhone" /></div>
        <div class="field"><label>事由</label><input v-model="form.purpose" /></div>
        <div class="field"><label>被访房屋</label><select v-model="form.houseId"><option value="">不关联</option><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select></div>
        <div class="field"><label>被访人</label><select v-model="form.personId"><option value="">不关联</option><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select></div>
        <div class="field"><label>开始</label><input v-model="form.validStart" type="datetime-local" /></div>
        <div class="field"><label>结束</label><input v-model="form.validEnd" type="datetime-local" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('access')" class="primary" :disabled="busy" @click="create">登记访客</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>通行记录</h2><span class="small muted">审批后生效</span></div>
      <div v-if="!records.length" class="empty">暂无访客记录</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>访客</th><th>手机号</th><th>被访房屋</th><th>被访人</th><th>事由</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ r.visitorName }}</td><td>{{ r.visitorPhone || '-' }}</td>
              <td>{{ r.houseName || '-' }}</td><td>{{ r.personName || '-' }}</td><td>{{ r.purpose || '-' }}</td>
              <td class="small">{{ r.validStart || '-' }} ~ {{ r.validEnd || '-' }}</td>
              <td><span class="badge" :class="statusClass(r.accessStatus)">{{ r.accessStatus }}</span></td>
              <td class="row">
                <button v-if="can('access') && r.accessStatus === 'PENDING'" class="sm" @click="approve(r, 'APPROVED')">通过</button>
                <button v-if="can('access') && r.accessStatus === 'PENDING'" class="sm danger" @click="approve(r, 'REJECTED')">拒绝</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
