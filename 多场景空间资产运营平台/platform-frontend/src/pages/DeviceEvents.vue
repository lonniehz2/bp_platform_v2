<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const project = ref(null)
const alerts = ref([])
const error = ref('')
const deviceAlerts = computed(() => alerts.value.filter(a => a.alertType === 'DEVICE'))

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  return all.find(p => String(p.id) === saved) || all[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (project.value) alerts.value = await api.alerts(project.value.id)
  } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>设备告警</h2><p>{{ project?.orgName || '未选择项目' }} · 低电量、拆机、离线、试错</p></div><span class="badge blue">{{ deviceAlerts.length }} 条</span></div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>设备告警列表</h2><RouterLink to="/alerts">全部告警</RouterLink></div>
      <div v-if="!deviceAlerts.length" class="empty">暂无设备告警</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>级别</th><th>标题</th><th>房屋</th><th>状态</th><th>处理人</th><th>时间</th></tr></thead>
          <tbody>
            <tr v-for="a in deviceAlerts" :key="a.id">
              <td><span class="badge" :class="a.alertLevel === 'HIGH' || a.alertLevel === 'URGENT' ? 'red' : 'orange'">{{ a.alertLevel }}</span></td>
              <td>{{ a.title }}</td><td>{{ a.houseName || '-' }}</td>
              <td><span class="badge" :class="a.alertStatus === 'RESOLVED' ? 'green' : 'orange'">{{ a.alertStatus }}</span></td>
              <td>{{ a.handlerName || '-' }}</td><td class="small">{{ a.createTime }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
