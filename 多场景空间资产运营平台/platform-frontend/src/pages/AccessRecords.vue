<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const records = ref([])
const error = ref('')
const busy = ref(false)

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) records.value = await api.accessRecords(project.value.id)
  } catch (e) { error.value = e.message }
}

async function approve(r, status) {
  busy.value = true; error.value = ''
  try { await api.approveAccessRecord(r.id, status); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>通行记录</h2><p>{{ project?.orgName || '未选择项目' }} · 访客通行登记和审批</p></div><span class="badge blue">{{ records.length }} 条</span></div>
      <div class="row"><RouterLink to="/access-records">登记访客</RouterLink></div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>通行列表</h2><span class="small muted">审批后生效</span></div>
      <div v-if="!records.length" class="empty">暂无通行记录</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>访客</th><th>手机号</th><th>被访房屋</th><th>被访人</th><th>有效期</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="r in records" :key="r.id">
              <td>{{ r.visitorName }}</td><td>{{ r.visitorPhone || '-' }}</td><td>{{ r.houseName || '-' }}</td>
              <td>{{ r.personName || '-' }}</td><td class="small">{{ r.validStart || '-' }} ~ {{ r.validEnd || '-' }}</td>
              <td><span class="badge" :class="r.accessStatus === 'APPROVED' ? 'green' : r.accessStatus === 'REJECTED' ? 'red' : 'orange'">{{ r.accessStatus }}</span></td>
              <td class="row">
                <button v-if="r.accessStatus === 'PENDING'" class="sm" :disabled="busy" @click="approve(r, 'APPROVED')">通过</button>
                <button v-if="r.accessStatus === 'PENDING'" class="sm danger" :disabled="busy" @click="approve(r, 'REJECTED')">拒绝</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
