<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const tasks = ref([])
const records = ref([])
const selectedTask = ref(null)
const error = ref('')
const busy = ref(false)

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red', APPROVING: 'orange' }[s] || '')

async function load() {
  error.value = ''
  try {
    tasks.value = await api.workflowTasks('')
    if (tasks.value.length) await selectTask(tasks.value[0])
  } catch (e) { error.value = e.message }
}

async function selectTask(task) {
  selectedTask.value = task
  records.value = await api.workflowRecords(task.id)
}

async function approve(task) {
  busy.value = true; error.value = ''
  try {
    await api.approveTask(task.id, { approverName: '审批人', comment: '通过' })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function reject(task) {
  busy.value = true; error.value = ''
  try {
    await api.rejectTask(task.id, { approverName: '审批人', comment: '驳回' })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div class="panel">
      <div class="panel-head"><div><h2>审批中心</h2><p>平台工作流任务 · 合同变更/退租等统一审批</p></div><span class="pill">{{ tasks.length }} 个任务</span></div>
      <div v-if="!tasks.length" class="empty">暂无审批任务</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>业务类型</th><th>摘要</th><th>提交人</th><th>当前节点</th><th>状态</th><th>提交时间</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="t in tasks" :key="t.id" @click="selectTask(t)" style="cursor:pointer">
              <td>{{ t.bizType }}</td><td>{{ t.summary }}</td><td>{{ t.submitterName }}</td>
              <td>{{ t.currentNode || '-' }}</td>
              <td><span class="badge" :class="statusClass(t.taskStatus)">{{ t.taskStatus }}</span></td>
              <td class="small">{{ t.submitTime }}</td>
              <td class="row">
                <button class="sm" v-if="t.taskStatus === 'APPROVING'" @click.stop="approve(t)">通过</button>
                <button class="sm danger" v-if="t.taskStatus === 'APPROVING'" @click.stop="reject(t)">驳回</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="panel" v-if="selectedTask">
      <div class="panel-head"><h2>审批记录</h2><span class="small muted">{{ selectedTask.bizType }} · {{ selectedTask.bizId }}</span></div>
      <div v-if="!records.length" class="empty">暂无记录</div>
      <div v-for="r in records" :key="r.id" class="row" style="border-bottom:1px solid var(--line);padding:9px 0">
        <div style="flex:1">
          <div>{{ r.nodeName }} · {{ r.action }}</div>
          <div class="small muted">{{ r.approverName }} · {{ r.comment || '无意见' }}</div>
        </div>
        <span class="mono">{{ r.actionTime }}</span>
      </div>
    </div>
  </div>
</template>
