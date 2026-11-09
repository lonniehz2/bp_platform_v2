<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import SearchSelect from '../components/SearchSelect.vue'
import { can } from '../permissions'

const project = ref(null)
const houses = ref([])
const persons = ref([])
const records = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ alertType: 'RISK', alertLevel: 'NORMAL', title: '', content: '', houseId: '', personId: '' })
const handleForm = reactive({ id: '', alertStatus: 'PROCESSING', handlerName: '运营中心', handleResult: '' })

const levelClass = (l) => ({ URGENT: 'red', HIGH: 'orange', NORMAL: 'blue' }[l] || '')
const statusClass = (s) => ({ RESOLVED: 'green', IGNORED: 'blue', PROCESSING: 'orange' }[s] || '')

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
    const [h, p, a] = await Promise.all([api.houses(id), api.persons(), api.alerts(id)])
    houses.value = h; persons.value = p; records.value = a
    if (!form.houseId && h.length) form.houseId = h[0].id
    if (!form.personId && p.length) form.personId = p[0].id
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error('请填写告警标题')
    await api.createAlert({
      projectId: project.value.id, alertType: form.alertType, alertLevel: form.alertLevel,
      title: form.title.trim(), content: form.content, houseId: form.houseId || null, personId: form.personId || null
    })
    form.title = ''; form.content = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

function openHandle(r) {
  handleForm.id = r.id; handleForm.alertStatus = 'PROCESSING'; handleForm.handleResult = ''
}

async function handle() {
  busy.value = true; error.value = ''
  try {
    await api.handleAlert(handleForm.id, {
      alertStatus: handleForm.alertStatus, handlerName: handleForm.handlerName, handleResult: handleForm.handleResult
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
      <div class="panel-head"><div><h2>风险告警</h2><p>{{ project?.orgName || '未选择项目' }} · 欠费、风险、设备、其他</p></div><span class="badge blue">{{ records.length }} 条</span></div>
      <div class="row">
        <div class="field"><label>类型</label><select v-model="form.alertType"><option value="RISK">风险</option><option value="OVERDUE">欠费</option><option value="DEVICE">设备</option><option value="OTHER">其他</option></select></div>
        <div class="field"><label>级别</label><select v-model="form.alertLevel"><option value="LOW">低</option><option value="NORMAL">普通</option><option value="HIGH">高</option><option value="URGENT">紧急</option></select></div>
        <div class="field" style="flex:2"><label>标题</label><input v-model="form.title" /></div>
        <div class="field"><label>房屋</label><SearchSelect v-model="form.houseId" :options="houses" label-key="houseCode" sublabel-key="houseName" value-key="id" placeholder="搜索房屋" clearable /></div>
        <div class="field"><label>人员</label><SearchSelect v-model="form.personId" :options="persons" label-key="personName" sublabel-key="personCode" value-key="id" placeholder="搜索人员" clearable /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('alert')" class="primary" :disabled="busy" @click="create">新增告警</button></div>
      </div>
      <div class="field" style="margin-top:8px"><label>内容</label><textarea v-model="form.content" rows="2" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>告警列表</h2><span class="small muted">处理中 → 已解决 / 忽略</span></div>
      <div v-if="!records.length" class="empty">暂无告警</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>类型</th><th>级别</th><th>标题</th><th>房屋</th><th>人员</th><th>状态</th><th>处理人</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ r.alertType }}</td><td><span class="badge" :class="levelClass(r.alertLevel)">{{ r.alertLevel }}</span></td>
              <td>{{ r.title }}</td><td>{{ r.houseName || '-' }}</td><td>{{ r.personName || '-' }}</td>
              <td><span class="badge" :class="statusClass(r.alertStatus)">{{ r.alertStatus }}</span></td>
              <td>{{ r.handlerName || '-' }}</td>
              <td><button v-if="can('alert') && r.alertStatus !== 'RESOLVED' && r.alertStatus !== 'IGNORED'" class="sm" @click="openHandle(r)">处理</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="handleForm.id" class="panel">
      <div class="panel-head"><h2>处理告警</h2><button class="sm" @click="handleForm.id = ''">关闭</button></div>
      <div class="row">
        <div class="field"><label>状态</label><select v-model="handleForm.alertStatus"><option value="PROCESSING">处理中</option><option value="RESOLVED">已解决</option><option value="IGNORED">忽略</option></select></div>
        <div class="field"><label>处理人</label><input v-model="handleForm.handlerName" /></div>
        <div class="field" style="flex:2"><label>处理结果</label><input v-model="handleForm.handleResult" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="handle">保存</button></div>
      </div>
    </div>
  </div>
</template>
