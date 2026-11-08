<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const tasks = ref([])
const records = ref([])
const selectedTask = ref(null)
const error = ref('')
const busy = ref(false)
const workflows = ref([])
const flowForm = reactive({ bizType: 'CONTRACT', orgId: '', flowName: '', nodeName: '合同审核', approverRole: 'REVIEWER' })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red', APPROVING: 'orange' }[s] || '')

async function load() {
  error.value = ''
  try {
    const [t, w] = await Promise.all([api.workflowTasks(''), api.workflows('GUARANTEE')])
    tasks.value = t; workflows.value = w
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


async function createWorkflow() {
  busy.value = true; error.value = ''
  try {
    if (!flowForm.flowName.trim() || !flowForm.bizType) throw new Error('请填写流程名称和业务类型')
    await api.createWorkflow({
      sceneCode: 'GUARANTEE',
      bizType: flowForm.bizType,
      orgId: flowForm.orgId ? Number(flowForm.orgId) : null,
      flowName: flowForm.flowName.trim(),
      nodes: [{ nodeName: flowForm.nodeName, approverRole: flowForm.approverRole }]
    })
    flowForm.flowName = ''
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

    <div class="panel">
      <div class="panel-head"><div><h2>审批模板</h2><p>场景默认流程 · 组织级覆盖</p></div><span class="pill">{{ workflows.length }} 个流程</span></div>
      <div class="row">
        <div class="field"><label>业务类型</label><select v-model="flowForm.bizType"><option value="CONTRACT">合同</option><option value="CONTRACT_CHANGE">合同变更</option><option value="BILL">账单</option><option value="APPLICATION">申请</option></select></div>
        <div class="field"><label>组织 ID（空为默认）</label><input v-model="flowForm.orgId" placeholder="可选" /></div>
        <div class="field" style="flex:2"><label>流程名称</label><input v-model="flowForm.flowName" /></div>
        <div class="field"><label>首节点</label><input v-model="flowForm.nodeName" /></div>
        <div class="field"><label>审批角色</label><input v-model="flowForm.approverRole" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="createWorkflow">新增流程</button></div>
      </div>
      <div v-if="!workflows.length" class="empty">暂无模板</div>
      <div v-for="w in workflows" :key="w.id" class="row" style="border-bottom:1px solid var(--line);padding:8px 0">
        <div style="flex:1"><div>{{ w.flowName }} · {{ w.bizType }}</div><div class="small muted">组织：{{ w.orgId || '默认' }} · 节点 {{ w.nodeCount }}</div></div>
        <span class="badge" :class="w.flowStatus === 'ENABLED' ? 'green' : 'orange'">{{ w.flowStatus }}</span>
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
