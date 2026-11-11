<script setup>
import { onMounted, reactive, ref } from 'vue'
import { enumLabel, enumText } from '../enumLabels'
import { api } from '../api'
import { useI18n } from 'vue-i18n'
import { currentScene } from '../scene'

const { t } = useI18n()
function nodeLabel(value) {
  return enumText(value)
}
const tasks = ref([])
const records = ref([])
const selectedTask = ref(null)
const error = ref('')
const busy = ref(false)
const workflows = ref([])
const flowForm = reactive({ bizType: 'CONTRACT', orgId: '', flowName: '', nodeName: t('audit.contract'), approverRole: 'REVIEWER' })

const statusClass = (s) => ({ APPROVED: 'green', REJECTED: 'red', APPROVING: 'orange' }[s] || '')

async function load() {
  error.value = ''
  try {
    const [t, w] = await Promise.all([api.workflowTasks(''), api.workflows(currentScene())])
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
    await api.approveTask(task.id, { approverName: t('audit.approver'), comment: t('audit.approvedComment') })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function reject(task) {
  busy.value = true; error.value = ''
  try {
    await api.rejectTask(task.id, { approverName: t('audit.approver'), comment: t('audit.rejectedComment') })
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function createWorkflow() {
  busy.value = true; error.value = ''
  try {
    if (!flowForm.flowName.trim() || !flowForm.bizType) throw new Error(t('audit.required'))
    await api.createWorkflow({
      sceneCode: currentScene(),
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
      <div class="panel-head"><div><h2>{{ t('audit.title') }}</h2><p>{{ t('audit.subtitle') }}</p></div><span class="pill">{{ tasks.length }} {{ t('audit.count') }}</span></div>
      <div v-if="!tasks.length" class="empty">{{ t('audit.empty') }}</div>
      <div class="table-wrap" v-else>
        <table>
          <thead><tr><th>{{ t('audit.bizType') }}</th><th>{{ t('audit.summary') }}</th><th>{{ t('audit.submitter') }}</th><th>{{ t('audit.currentNode') }}</th><th>{{ t('audit.status') }}</th><th>{{ t('audit.submitTime') }}</th><th>{{ t('audit.action') }}</th></tr></thead>
          <tbody>
            <tr v-for="t in tasks" :key="t.id" @click="selectTask(t)" style="cursor:pointer">
              <td>{{ enumLabel(t.bizType) }}</td><td>{{ enumText(t.summary) }}</td><td>{{ t.submitterName }}</td>
              <td>{{ t.currentNode ? enumText(t.currentNode) : '-' }}</td>
              <td><span class="badge" :class="statusClass(t.taskStatus)">{{ enumLabel(t.taskStatus) }}</span></td>
              <td class="small">{{ t.submitTime }}</td>
              <td class="row">
                <button class="sm" v-if="t.taskStatus === 'APPROVING'" @click.stop="approve(t)">{{ t('audit.approve') }}</button>
                <button class="sm danger" v-if="t.taskStatus === 'APPROVING'" @click.stop="reject(t)">{{ t('audit.reject') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="panel">
      <div class="panel-head"><div><h2>{{ t('audit.templates') }}</h2><p>{{ t('audit.templatesHint') }}</p></div><span class="pill">{{ workflows.length }} {{ t('audit.flowCount') }}</span></div>
      <div class="row">
        <div class="field"><label>{{ t('audit.bizType') }}</label><select v-model="flowForm.bizType"><option value="CONTRACT">{{ t('audit.contract') }}</option><option value="CONTRACT_CHANGE">{{ t('audit.contractChange') }}</option><option value="BILL">{{ t('audit.bill') }}</option><option value="APPLICATION">{{ t('audit.application') }}</option></select></div>
        <div class="field"><label>{{ t('audit.orgId') }}</label><input v-model="flowForm.orgId" :placeholder="t('audit.optional')" /></div>
        <div class="field" style="flex:2"><label>{{ t('audit.flowName') }}</label><input v-model="flowForm.flowName" /></div>
        <div class="field"><label>{{ t('audit.firstNode') }}</label><input v-model="flowForm.nodeName" /></div>
        <div class="field"><label>{{ t('audit.approverRole') }}</label><input v-model="flowForm.approverRole" /></div>
        <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button class="primary" :disabled="busy" @click="createWorkflow">{{ t('audit.addFlow') }}</button></div>
      </div>
      <div v-if="!workflows.length" class="empty">{{ t('audit.noTemplates') }}</div>
      <div v-for="w in workflows" :key="w.id" class="row" style="border-bottom:1px solid var(--line);padding:8px 0">
        <div style="flex:1"><div>{{ enumText(w.flowName) }} · {{ enumLabel(w.bizType) }}</div><div class="small muted">{{ t('audit.org') }}: {{ w.orgId || t('audit.defaultOrg') }} · {{ t('audit.nodes') }} {{ w.nodeCount }}</div></div>
        <span class="badge" :class="w.flowStatus === 'ENABLED' ? 'green' : 'orange'">{{ enumLabel(w.flowStatus) }}</span>
      </div>
    </div>

    <div class="panel" v-if="selectedTask">
      <div class="panel-head"><h2>{{ t('audit.records') }}</h2><span class="small muted">{{ enumLabel(selectedTask.bizType) }} · {{ selectedTask.bizId }}</span></div>
      <div v-if="!records.length" class="empty">{{ t('audit.noRecords') }}</div>
      <div v-for="r in records" :key="r.id" class="row" style="border-bottom:1px solid var(--line);padding:9px 0">
        <div style="flex:1">
          <div>{{ nodeLabel(r.nodeName) }} · {{ enumLabel(r.action) }}</div>
          <div class="small muted">{{ r.approverName }} · {{ r.comment || t('audit.noComment') }}</div>
        </div>
        <span class="mono">{{ r.actionTime }}</span>
      </div>
    </div>
  </div>
</template>
