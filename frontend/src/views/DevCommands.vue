<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">设备指令</h3>
      <el-tag size="small" type="info">经 IoT 平台下发 · 不直连设备</el-tag>
      <div class="spacer" />
      <el-select v-model="query.status" placeholder="状态" clearable style="width:120px"
                 @change="reload">
        <el-option label="待下发" value="PENDING" />
        <el-option label="已下发" value="SENT" />
        <el-option label="成功" value="SUCCESS" />
        <el-option label="失败" value="FAILED" />
        <el-option label="超时" value="TIMEOUT" />
        <el-option label="已取消" value="CANCELED" />
      </el-select>
      <el-select v-model="query.commandType" placeholder="指令类型" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="t in TYPES" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <DeviceSelect v-model="query.deviceId" width="240px" testid="device-select" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="openCreate">新建指令</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
              title="指令经 IoT 平台下发，回执由 IoT 回调回填；超时（默认 10 秒）会自动重试，最多 3 次。" />

    <el-table empty-text="暂无设备指令" :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="commandNo" label="指令号" width="180" />
      <el-table-column label="类型" width="130">
        <template #default="{ row }">{{ typeLabel(row.commandType) }}</template>
      </el-table-column>
      <el-table-column prop="deviceId" label="设备" width="150" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resultMsg" label="结果" min-width="180"
                       show-overflow-tooltip>
        <template #default="{ row }">{{ row.resultMsg || '—' }}</template>
      </el-table-column>
      <el-table-column prop="retryCount" label="重试" width="70" />
      <el-table-column prop="costMs" label="耗时(ms)" width="90" />
      <el-table-column prop="operatorName" label="操作人" width="110">
        <template #default="{ row }">{{ row.operatorName || '—' }}</template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" min-width="165" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.commandType === 'METER_SWITCH'
                     && row.approveStatus === 'PENDING'"
                     link type="warning" @click="approve(row, true)">通过</el-button>
          <el-button v-if="row.commandType === 'METER_SWITCH'
                     && row.approveStatus === 'PENDING'"
                     link type="danger" @click="approve(row, false)">驳回</el-button>
          <el-button link type="primary"
                     :disabled="['SUCCESS', 'CANCELED'].includes(row.status)"
                     @click="retry(row)">重试</el-button>
          <el-button link :disabled="row.status !== 'PENDING'"
                     @click="cancel(row)">取消</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize" :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <el-dialog v-model="createVisible" title="新建设备指令" width="560px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="指令类型" required>
          <el-select v-model="form.commandType" style="width:100%">
            <el-option v-for="t in TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="设备" required>
          <el-select v-model="form.deviceId" filterable style="width:100%">
            <el-option v-for="d in devices" :key="d.deviceId"
                       :label="(d.deviceName || d.deviceId) + '（' + d.deviceId + '）'"
                       :value="d.deviceId" />
          </el-select>
        </el-form-item>
        <el-form-item label="原因" required>
          <el-input v-model="form.reason" placeholder="如：住户报修远程开门" />
        </el-form-item>
        <el-form-item v-if="form.commandType === 'METER_SWITCH'" label="表号">
          <el-input v-model="form.meterNo" placeholder="拉合闸时填写表号" />
        </el-form-item>
      </el-form>
      <el-alert v-if="form.commandType === 'METER_SWITCH'" type="warning" :closable="false"
                show-icon title="拉合闸需审批通过后才下发；拉闸默认延迟执行，可在窗口内取消。" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="指令详情" size="480px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="指令号">{{ detail?.commandNo }}</el-descriptions-item>
        <el-descriptions-item label="请求号">{{ detail?.requestId }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ typeLabel(detail?.commandType) }}</el-descriptions-item>
        <el-descriptions-item label="设备">{{ detail?.deviceId }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel(detail?.status) }}</el-descriptions-item>
        <el-descriptions-item label="结果码">{{ detail?.resultCode || '—' }}</el-descriptions-item>
        <el-descriptions-item label="结果说明">{{ detail?.resultMsg || '—' }}</el-descriptions-item>
        <el-descriptions-item label="下发时间">{{ detail?.dispatchTime || '—' }}</el-descriptions-item>
        <el-descriptions-item label="回执时间">{{ detail?.ackTime || '—' }}</el-descriptions-item>
        <el-descriptions-item label="耗时(ms)">{{ detail?.costMs ?? '—' }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ detail?.operatorName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="原因">{{ detail?.reason || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup>
/**
 * 设备指令：远程开锁 / 重启 / 校时 / 拉合闸。
 *
 * 平台不直连设备，指令经 IoT 平台下发，结果由回调 command/ack 回填。
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import DeviceSelect from '@/components/DeviceSelect.vue'

const TYPES = [
  { value: 'LOCK_OPEN', label: '远程开锁' },
  { value: 'DEVICE_REBOOT', label: '远程重启' },
  { value: 'DEVICE_SYNC_TIME', label: '远程校时' },
  { value: 'METER_SWITCH', label: '电表拉合闸' }
]

const STATUS = {
  PENDING: { label: '待下发', type: 'warning' },
  SENT: { label: '已下发', type: 'info' },
  SUCCESS: { label: '成功', type: 'success' },
  FAILED: { label: '失败', type: 'danger' },
  TIMEOUT: { label: '超时', type: 'danger' },
  CANCELED: { label: '已取消', type: 'info' }
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
