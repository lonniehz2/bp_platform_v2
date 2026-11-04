<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('devCmd.title') }}</h3>
      <el-tag size="small" type="info">{{ t('miscPage.devCmdBadge') }}</el-tag>
      <div class="spacer" />
      <el-select v-model="query.status" :placeholder="t('devCmd.status')" clearable style="width:120px"
                 @change="reload">
        <el-option :label="t('devCmd.pending')" value="PENDING" />
        <el-option :label="t('devCmd.sent')" value="SENT" />
        <el-option :label="t('devCmd.success')" value="SUCCESS" />
        <el-option :label="t('devCmd.failed')" value="FAILED" />
        <el-option :label="t('devCmd.timeout')" value="TIMEOUT" />
        <el-option :label="t('devCmd.canceled')" value="CANCELED" />
      </el-select>
      <el-select v-model="query.commandType" :placeholder="t('devCmd.cmdType')" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="t in TYPES" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <DeviceSelect v-model="query.deviceId" width="240px" testid="device-select" />
      <el-button type="primary" @click="reload">{{ t('devCmd.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('devCmd.reset') }}</el-button>
      <el-button type="success" @click="openCreate">{{ t('devCmd.create') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
              :title="t('miscPage.devCmdTip')" />

    <el-table :empty-text="t('devCmd.noCommands')" :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="commandNo" :label="t('devCmd.no')" width="180" />
      <el-table-column :label="t('devCmd.type')" width="130">
        <template #default="{ row }">{{ typeLabel(row.commandType) }}</template>
      </el-table-column>
      <el-table-column prop="deviceId" :label="t('devCmd.device')" width="150" />
      <el-table-column :label="t('devCmd.status')" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resultMsg" :label="t('devCmd.result')" min-width="180"
                       show-overflow-tooltip>
        <template #default="{ row }">{{ resultText(row.resultMsg) }}</template>
      </el-table-column>
      <el-table-column prop="retryCount" :label="t('devCmd.retry')" width="70" />
      <el-table-column prop="costMs" :label="t('devCmd.cost')" width="90" />
      <el-table-column prop="operatorName" :label="t('devCmd.operator')" width="110">
        <template #default="{ row }">{{ row.operatorName || '—' }}</template>
      </el-table-column>
      <el-table-column prop="createTime" :label="t('devCmd.created')" min-width="165" />
      <el-table-column :label="t('devCmd.actions')" width="200" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.commandType === 'METER_SWITCH'
                     && row.approveStatus === 'PENDING'"
                     link type="warning" @click="approve(row, true)">{{ t('devCmd.approve') }}</el-button>
          <el-button v-if="row.commandType === 'METER_SWITCH'
                     && row.approveStatus === 'PENDING'"
                     link type="danger" @click="approve(row, false)">{{ t('devCmd.reject') }}</el-button>
          <el-button link type="primary"
                     :disabled="['SUCCESS', 'CANCELED'].includes(row.status)"
                     @click="retry(row)">{{ t('devCmd.retryAction') }}</el-button>
          <el-button link :disabled="row.status !== 'PENDING'"
                     @click="cancel(row)">{{ t('devCmd.cancel') }}</el-button>
          <el-button link @click="detail = row; show = true">{{ t('devCmd.detail') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="query.pageSize" :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />

    <el-dialog v-model="createVisible" :title="t('devCmd.createTitle')" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item :label="t('devCmd.cmdType')" required>
          <el-select v-model="form.commandType" style="width:100%">
            <el-option v-for="t in TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('devCmd.device')" required>
          <el-select v-model="form.deviceId" filterable style="width:100%">
            <el-option v-for="d in devices" :key="d.deviceId"
                       :label="(d.deviceName || d.deviceId) + '（' + d.deviceId + '）'"
                       :value="d.deviceId" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('devCmd.reason')" required>
          <el-input v-model="form.reason" :placeholder="t('devCmd.reasonHint')" />
        </el-form-item>
        <el-form-item v-if="form.commandType === 'METER_SWITCH'" :label="t('devCmd.meterNo')">
          <el-input v-model="form.meterNo" :placeholder="t('devCmd.meterHint')" />
        </el-form-item>
      </el-form>
      <el-alert v-if="form.commandType === 'METER_SWITCH'" type="warning" :closable="false"
                show-icon :title="t('miscPage.devCmdApproval')" />
      <template #footer>
        <el-button @click="createVisible = false">{{ t('devCmd.cancelBtn') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('devCmd.submit') }}</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" :title="t('devCmd.drawer')" size="480px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item :label="t('devCmd.no')">{{ detail?.commandNo }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.requestNo')">{{ detail?.requestId }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.type')">{{ typeLabel(detail?.commandType) }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.device')">{{ detail?.deviceId }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.status')">{{ statusLabel(detail?.status) }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.resultCode')">{{ detail?.resultCode || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.resultMsg')">{{ resultText(detail?.resultMsg) }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.dispatchTime')">{{ detail?.dispatchTime || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.ackTime')">{{ detail?.ackTime || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.cost')">{{ detail?.costMs ?? '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.operator')">{{ detail?.operatorName || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('devCmd.reasonLabel')">{{ detail?.reason || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * 设备指令：远程开锁 / 重启 / 校时 / 拉合闸。
 *
 * 平台不直连设备，指令经 IoT 平台下发，结果由回调 command/ack 回填。
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import DeviceSelect from '@/components/DeviceSelect.vue'

const { t } = useI18n()
const TYPES = [
  { value: 'LOCK_OPEN', label: t('devCmd.lockOpen') },
  { value: 'DEVICE_REBOOT', label: t('devCmd.reboot') },
  { value: 'DEVICE_SYNC_TIME', label: t('devCmd.syncTime') },
  { value: 'LOCK_ALWAYS_OPEN', label: t('devCmd.alwaysOpen') },
  { value: 'LOCK_ALWAYS_CLOSE', label: t('devCmd.alwaysClose') },
  { value: 'LOCK_MODE_NORMAL', label: t('devCmd.normalMode') },
  { value: 'METER_SWITCH', label: t('devCmd.meterSwitch') }
]

const STATUS = {
  PENDING: { label: t('devCmd.pending'), type: 'warning' },
  SENT: { label: t('devCmd.sent'), type: 'info' },
  SUCCESS: { label: t('devCmd.success'), type: 'success' },
  FAILED: { label: t('devCmd.failed'), type: 'danger' },
  TIMEOUT: { label: t('devCmd.timeout'), type: 'danger' },
  CANCELED: { label: t('devCmd.canceled'), type: 'info' }
}

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const createVisible = ref(false)
const show = ref(false)
const detail = ref(null)
const devices = ref([])
const query = reactive({ pageNum: 1, pageSize: 20, status: '', commandType: '', deviceId: '' })
const form = reactive({ commandType: 'LOCK_OPEN', deviceId: '', reason: '', meterNo: '' })

function typeLabel(v) {
  const t = TYPES.find((x) => x.value === v)
  return t ? t.label : (v || '—')
}
function statusLabel(v) { return (STATUS[v] || {}).label || v || '—' }
function statusType(v) { return (STATUS[v] || {}).type || 'info' }

function resultText(v) {
  if (!v) return '—'
  const key = String(v).trim().toLowerCase()
  const map = {
    ok: t('devCmd.success'), success: t('devCmd.success'), 'mock ok': t('devCmd.resultMockOk'),
    failed: t('devCmd.failed'), fail: t('devCmd.failed'), timeout: t('devCmd.timeout'), error: t('devCmd.resultError')
  }
  return map[key] || v
}

async function load() {
  loading.value = true
  try {
    const d = await req.get('/dev-commands', {
      params: { pageNum: query.pageNum, pageSize: query.pageSize,
        status: query.status || undefined,
        commandType: query.commandType || undefined,
        deviceId: query.deviceId || undefined }
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } catch (e) {
    rows.value = []; total.value = 0
  } finally { loading.value = false }
}

async function loadDevices() {
  try {
    const d = await req.get('/devices', { params: { pageNum: 1, pageSize: 200 } })
    devices.value = d.rows || []
  } catch (e) { devices.value = [] }
}

function reload() { query.pageNum = 1; load() }
function resetQuery() {
  Object.assign(query, { pageNum: 1, status: '', commandType: '', deviceId: '' })
  load()
}

function openCreate() {
  Object.assign(form, { commandType: 'LOCK_OPEN', deviceId: '', reason: '', meterNo: '' })
  createVisible.value = true
}

async function doCreate() {
  if (!form.deviceId || !form.reason) {
    ElMessage.warning('设备与原因不能为空'); return
  }
  saving.value = true
  try {
    await req.post('/dev-commands', { ...form })
    ElMessage.success('指令已提交')
    createVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '提交失败')
  } finally { saving.value = false }
}

async function retry(row) {
  await ElMessageBox.confirm(`确认重试指令「${row.commandNo}」？`, '重试', { type: 'warning' })
  await req.post(`/dev-commands/${row.id}/retry`)
  ElMessage.success('已重试')
  load()
}

async function cancel(row) {
  await ElMessageBox.confirm(`确认取消指令「${row.commandNo}」？`, '取消', { type: 'warning' })
  await req.post(`/dev-commands/${row.id}/cancel`)
  ElMessage.success('已取消')
  load()
}

async function approve(row, pass) {
  await ElMessageBox.confirm(
    `${pass ? '通过' : '驳回'}拉合闸指令「${row.commandNo}」？`, '审批', { type: 'warning' })
  await req.post(`/dev-commands/${row.id}/approve`, null, { params: { approve: pass } })
  ElMessage.success('已处理')
  load()
}

onMounted(() => { load(); loadDevices() })
</script>
