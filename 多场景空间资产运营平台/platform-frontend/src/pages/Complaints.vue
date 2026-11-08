<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const houses = ref([])
const persons = ref([])
const records = ref([])
const type = ref('')
const error = ref('')
const busy = ref(false)
const form = reactive({ complaintType: 'COMPLAINT', title: '', content: '', houseId: '', personId: '' })
const handleForm = reactive({ id: '', complaintStatus: 'PROCESSING', handlerName: '客服中心', handleResult: '' })

const typeName = (t) => ({ COMPLAINT: '投诉', APPEAL: '申诉', VISIT: '走访' }[t] || t)
const statusClass = (s) => ({ RESOLVED: 'green', CLOSED: 'blue', PROCESSING: 'orange' }[s] || '')

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
    const [h, p, c] = await Promise.all([api.houses(id), api.persons(), api.complaints(id, type.value)])
    houses.value = h; persons.value = p; records.value = c
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error('请填写标题')
    await api.createComplaint({
      projectId: project.value.id, complaintType: form.complaintType, title: form.title.trim(),
      content: form.content, houseId: form.houseId || null, personId: form.personId || null
    })
    form.title = ''; form.content = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function openHandle(r) {
  handleForm.id = r.id
  handleForm.complaintStatus = 'PROCESSING'
  handleForm.handleResult = ''
}

async function handle() {
  busy.value = true; error.value = ''
  try {
    await api.handleComplaint(handleForm.id, {
      complaintStatus: handleForm.complaintStatus,
      handlerName: handleForm.handlerName,
      handleResult: handleForm.handleResult
    })
    handleForm.id = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>投诉与申诉</h2><p>{{ project?.orgName || '未选择项目' }} · 投诉、申诉、入户走访</p></div>
        <select v-model="type" @change="load" style="width:140px"><option value="">全部</option><option value="COMPLAINT">投诉</option><option value="APPEAL">申诉</option><option value="VISIT">走访</option></select>
      </div>
      <div class="row">
        <div class="field"><label>类型</label><select v-model="form.complaintType"><option value="COMPLAINT">投诉</option><option value="APPEAL">申诉</option><option value="VISIT">走访</option></select></div>
        <div class="field" style="flex:2"><label>标题</label><input v-model="form.title" /></div>
        <div class="field"><label>房屋</label><select v-model="form.houseId"><option value="">不关联</option><option v-for="h in houses" :key="h.id" :value="h.id">{{ h.houseCode }} · {{ h.houseName }}</option></select></div>
        <div class="field"><label>人员</label><select v-model="form.personId"><option value="">不关联</option><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('complaint')" class="primary" :disabled="busy" @click="create">新增记录</button></div>
      </div>
      <div class="field" style="margin-top:8px"><label>内容</label><textarea v-model="form.content" rows="2" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>记录列表</h2><span class="small muted">{{ records.length }} 条</span></div>
      <div v-if="!records.length" class="empty">暂无记录</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>类型</th><th>标题</th><th>房屋</th><th>人员</th><th>状态</th><th>处理人</th><th>结果</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ typeName(r.complaintType) }}</td><td>{{ r.title }}</td>
              <td>{{ r.houseName || '-' }}</td><td>{{ r.personName || '-' }}</td>
              <td><span class="badge" :class="statusClass(r.complaintStatus)">{{ r.complaintStatus }}</span></td>
              <td>{{ r.handlerName || '-' }}</td><td class="small">{{ r.handleResult || '-' }}</td>
              <td><button v-if="can('complaint') && r.complaintStatus !== 'CLOSED'" class="sm" @click="openHandle(r)">处理</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="handleForm.id" class="panel">
      <div class="panel-head"><h2>处理记录</h2><button class="sm" @click="handleForm.id = ''">关闭</button></div>
      <div class="row">
        <div class="field"><label>状态</label><select v-model="handleForm.complaintStatus"><option value="PROCESSING">处理中</option><option value="RESOLVED">已解决</option><option value="CLOSED">已关闭</option></select></div>
        <div class="field"><label>处理人</label><input v-model="handleForm.handlerName" /></div>
        <div class="field" style="flex:2"><label>处理结果</label><input v-model="handleForm.handleResult" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="handle">保存</button></div>
      </div>
    </div>
  </div>
</template>
