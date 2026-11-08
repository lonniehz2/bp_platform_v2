<template>
  <div class="dunning-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyDunning.noProject')" />
    <el-card shadow="never">
      <div class="toolbar">
        <div>
          <div class="title">{{ t('propertyDunning.title') }}</div>
          <div class="sub">{{ t('propertyDunning.hint') }}</div>
        </div>
        <div class="spacer" />
        <el-input v-model="keyword" :placeholder="t('propertyDunning.search')" clearable
                  style="width:180px" @keyup.enter="loadArrears" />
        <el-checkbox-group v-model="channels">
          <el-checkbox label="SMS">{{ t('propertyDunning.sms') }}</el-checkbox>
          <el-checkbox label="WECHAT">{{ t('propertyDunning.wechat') }}</el-checkbox>
        </el-checkbox-group>
        <el-button type="primary" :disabled="!selected.length" @click="send">
          {{ t('propertyDunning.send', { n: selected.length }) }}
        </el-button>
      </div>
      <el-table :data="arrears" border size="small" @selection-change="(v) => (selected = v)">
        <el-table-column type="selection" width="46" />
        <el-table-column prop="billNo" :label="t('propertyDunning.billNo')" width="190" />
        <el-table-column prop="houseName" :label="t('propertyDunning.house')" min-width="170" />
        <el-table-column prop="payerName" :label="t('propertyDunning.payer')" width="150" />
        <el-table-column prop="phone" :label="t('propertyDunning.phone')" width="130" />
        <el-table-column prop="payableAmount" :label="t('propertyDunning.amount')" width="110" />
        <el-table-column prop="paidAmount" :label="t('propertyDunning.paid')" width="100" />
        <el-table-column prop="dueDate" :label="t('propertyDunning.dueDate')" width="120" />
        <el-table-column prop="billStatus" :label="t('propertyDunning.status')" width="100" />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <template #header>{{ t('propertyDunning.tasks') }}</template>
      <el-table :data="tasks" border size="small">
        <el-table-column prop="taskNo" :label="t('propertyDunning.taskNo')" width="210" />
        <el-table-column prop="channels" :label="t('propertyDunning.channels')" width="130" />
        <el-table-column prop="totalCount" :label="t('propertyDunning.total')" width="90" />
        <el-table-column prop="successCount" :label="t('propertyDunning.success')" width="90" />
        <el-table-column prop="createTime" :label="t('propertyDunning.sendTime')" width="180" />
        <el-table-column :label="t('propertyDunning.actions')" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="openRecords(row)">{{ t('propertyDunning.records') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="recordVisible" :title="t('propertyDunning.records')" width="720px">
      <el-table :data="records" border size="small" max-height="360">
        <el-table-column prop="payerName" :label="t('propertyDunning.payer')" width="130" />
        <el-table-column prop="houseName" :label="t('propertyDunning.house')" min-width="150" />
        <el-table-column prop="amount" :label="t('propertyDunning.amount')" width="90" />
        <el-table-column prop="channel" :label="t('propertyDunning.channels')" width="90" />
        <el-table-column prop="recipient" :label="t('propertyDunning.phone')" width="130" />
        <el-table-column prop="sendStatus" :label="t('propertyDunning.status')" width="90" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { usePropertyStore } from '@/store/property'

const { t } = useI18n()
const store = usePropertyStore()
const projectId = computed(() => store.projectId)
const keyword = ref('')
const channels = ref(['SMS'])
const arrears = ref([])
const selected = ref([])
const tasks = ref([])
const records = ref([])
const recordVisible = ref(false)

onMounted(async () => {
  await store.loadProjects()
  await loadAll()
})
watch(projectId, loadAll)

async function loadAll() { await Promise.all([loadArrears(), loadTasks()]) }

async function loadArrears() {
  if (!projectId.value) return
  try {
    arrears.value = await req.get('/property/dunning/arrears', {
      params: { projectId: projectId.value, keyword: keyword.value || undefined }
    }) || []
  } catch (e) { ElMessage.error(t('propertyDunning.loadFailed')) }
}

async function loadTasks() {
  if (!projectId.value) return
  try {
    tasks.value = await req.get('/property/dunning/tasks', { params: { projectId: projectId.value } }) || []
  } catch (e) { tasks.value = [] }
}

async function send() {
  if (!channels.value.length) {
    ElMessage.warning(t('propertyDunning.channelRequired'))
    return
  }
  try {
    const r = await req.post('/property/dunning/tasks', {
      billIds: selected.value.map((b) => b.billId),
      channels: channels.value.join(','),
      reason: t('propertyDunning.defaultReason')
    }, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyDunning.sent', { success: r.success, fail: r.fail }))
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyDunning.sendFailed'))
  }
}

async function openRecords(row) {
  records.value = await req.get(`/property/dunning/tasks/${row.id}/records`) || []
  recordVisible.value = true
}
</script>

<style scoped>
.dunning-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.sub { font-size: 12px; color: #8492a6; margin-top: 3px; }
.spacer { flex: 1; }
</style>
