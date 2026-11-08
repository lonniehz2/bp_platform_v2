<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const tasks = ref([])
const status = ref('')
const error = ref('')
const filtered = computed(() => status.value ? tasks.value.filter(t => t.taskStatus === status.value) : tasks.value)

async function load() {
  error.value = ''
  try { tasks.value = await api.workflowTasks(status.value) } catch (e) { error.value = e.message }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>我的待办</h2><p>待受理、待审批、待处理任务</p></div><span class="badge blue">{{ filtered.length }} 个任务</span></div>
      <div class="row">
        <div class="field"><label>状态</label><select v-model="status" @change="load"><option value="">全部</option><option value="APPROVING">审批中</option><option value="APPROVED">已通过</option><option value="REJECTED">已驳回</option></select></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><RouterLink to="/audit">进入审批中心</RouterLink></div>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><h2>待办列表</h2><span class="small muted">按业务提交时间倒序</span></div>
      <div v-if="!filtered.length" class="empty">暂无待办</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>业务类型</th><th>摘要</th><th>提交人</th><th>当前节点</th><th>状态</th><th>提交时间</th></tr></thead>
          <tbody>
            <tr v-for="t in filtered" :key="t.id">
              <td>{{ t.bizType }}</td><td>{{ t.summary }}</td><td>{{ t.submitterName }}</td>
              <td>{{ t.currentNode || '-' }}</td>
              <td><span class="badge" :class="t.taskStatus === 'APPROVED' ? 'green' : t.taskStatus === 'REJECTED' ? 'red' : 'orange'">{{ t.taskStatus }}</span></td>
              <td class="small">{{ t.submitTime }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
