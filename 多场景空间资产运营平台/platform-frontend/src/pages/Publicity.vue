<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import { can } from '../permissions'

const project = ref(null)
const records = ref([])
const error = ref('')
const busy = ref(false)
const form = reactive({ publicityType: 'ALLOCATION', title: '', content: '', startDate: '', endDate: '' })
const typeName = (t) => ({ ALLOCATION: '配租公示', QUALIFICATION: '资格公示', EXIT: '退出公示', POLICY: '政策公示' }[t] || t)
const statusClass = (s) => ({ PUBLISHED: 'green', CLOSED: 'blue' }[s] || 'orange')

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) records.value = await api.publicities(project.value.id)
  } catch (e) { error.value = e.message }
}

async function create() {
  busy.value = true; error.value = ''
  try {
    if (!form.title.trim()) throw new Error('请填写公示标题')
    await api.createPublicity({
      projectId: project.value.id, publicityType: form.publicityType, title: form.title.trim(),
      content: form.content, startDate: form.startDate || null, endDate: form.endDate || null
    })
    form.title = ''; form.content = ''
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function update(r, status) {
  busy.value = true; error.value = ''
  try {
    await api.updatePublicityStatus(r.id, status)
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>公示管理</h2><p>{{ project?.orgName || '未选择项目' }} · 配租、资格、退出、政策公示</p></div><span class="badge blue">{{ records.length }} 条</span></div>
      <div class="row">
        <div class="field"><label>类型</label><select v-model="form.publicityType"><option value="ALLOCATION">配租公示</option><option value="QUALIFICATION">资格公示</option><option value="EXIT">退出公示</option><option value="POLICY">政策公示</option></select></div>
        <div class="field" style="flex:2"><label>标题</label><input v-model="form.title" /></div>
        <div class="field"><label>开始</label><input v-model="form.startDate" type="date" /></div>
        <div class="field"><label>结束</label><input v-model="form.endDate" type="date" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('publicity')" class="primary" :disabled="busy" @click="create">新建公示</button></div>
      </div>
      <div class="field" style="margin-top:8px"><label>内容</label><textarea v-model="form.content" rows="2" /></div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>公示列表</h2><span class="small muted">草稿 → 发布 → 关闭</span></div>
      <div v-if="!records.length" class="empty">暂无公示</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>类型</th><th>标题</th><th>公示期</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ typeName(r.publicityType) }}</td><td>{{ r.title }}</td>
              <td class="small">{{ r.startDate || '-' }} ~ {{ r.endDate || '-' }}</td>
              <td><span class="badge" :class="statusClass(r.publicityStatus)">{{ r.publicityStatus }}</span></td>
              <td class="row">
                <button v-if="can('publicity') && r.publicityStatus === 'DRAFT'" class="sm" @click="update(r, 'PUBLISHED')">发布</button>
                <button v-if="can('publicity') && r.publicityStatus === 'PUBLISHED'" class="sm" @click="update(r, 'CLOSED')">关闭</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
