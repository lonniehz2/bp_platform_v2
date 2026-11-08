<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const persons = ref([])
const spaces = ref([])
const grants = ref([])
const personId = ref('')
const error = ref('')
const busy = ref(false)
const form = reactive({ targetId: '', validStart: '2026-11-08', validEnd: '2027-11-07' })

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
    const [p, s] = await Promise.all([api.persons(), api.spaces(project.value.id)])
    persons.value = p; spaces.value = s
    if (!personId.value && p.length) personId.value = p[0].id
    if (!form.targetId && s.length) form.targetId = s[0].id
    await loadGrants()
  } catch (e) { error.value = e.message }
}

async function loadGrants() {
  if (!personId.value) { grants.value = []; return }
  try { grants.value = await api.grants(personId.value, project.value?.id) } catch { grants.value = [] }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!personId.value || !form.targetId) throw new Error('请选择人员和授权空间')
    await api.createGrant({
      projectId: project.value.id, personId: personId.value, targetType: 'SPACE', targetId: form.targetId,
      grantLevel: 'OPEN', validStart: form.validStart, validEnd: form.validEnd, sourceType: 'MANUAL'
    })
    await loadGrants()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function revoke(g) {
  busy.value = true; error.value = ''
  try { await api.revokeGrant(g.id, '授权撤销'); await loadGrants() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>通行授权</h2><p>{{ project?.orgName || '未选择项目' }} · 人员到空间的通行授权</p></div><span class="badge blue">{{ grants.length }} 条</span></div>
      <div class="row">
        <div class="field"><label>人员</label><select v-model="personId" @change="loadGrants"><option v-for="p in persons" :key="p.id" :value="p.id">{{ p.personName }}</option></select></div>
        <div class="field"><label>授权空间</label><select v-model="form.targetId"><option v-for="s in spaces" :key="s.id" :value="s.id">{{ s.spaceName }}</option></select></div>
        <div class="field"><label>开始</label><input v-model="form.validStart" type="date" /></div>
        <div class="field"><label>结束</label><input v-model="form.validEnd" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="create">新增授权</button></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>授权列表</h2><span class="small muted">授权到空间，按人员查看</span></div>
      <div v-if="!grants.length" class="empty">暂无授权</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>类型</th><th>对象</th><th>级别</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="g in grants" :key="g.id">
              <td>{{ g.targetType }}</td><td class="mono">{{ g.targetId }}</td><td>{{ g.grantLevel }}</td>
              <td class="small">{{ g.validStart }} ~ {{ g.validEnd || '长期' }}</td>
              <td><span class="badge" :class="g.grantStatus === 'ACTIVE' ? 'green' : 'orange'">{{ g.grantStatus }}</span></td>
              <td><button v-if="g.grantStatus === 'ACTIVE'" class="sm danger" :disabled="busy" @click="revoke(g)">撤销</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
