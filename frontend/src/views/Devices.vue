<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('device.title') }}</h3>
      <el-tag size="small" type="info">
        {{ t('misc2.onlineOf', { online: stats.online ?? 0, total: stats.total ?? 0 }) }}
        （{{ stats.onlineRate ?? 0 }}%）
      </el-tag>
      <div class="spacer" />
      <SpaceSelect v-model="query.spaceId" width="210px" testid="spaceselect" />
      <el-select v-model="query.deviceType" :placeholder="t('device.type')" clearable
                 style="width:150px" @change="load">
        <el-option v-for="t in devTypes" :key="t.code" :value="t.code"
                   :label="t.label + (t.count ? '（' + t.count + '）' : '')" />
      </el-select>
      <el-select v-model="query.onlineStatus" :placeholder="t('device.onlineStatus')" clearable
                 style="width:130px" @change="load">
        <el-option :label="t('device.online')" :value="1" />
        <el-option :label="t('device.offline')" :value="0" />
      </el-select>
      <el-button type="primary" @click="load">{{ t('device.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('device.reset') }}</el-button>
      <el-button type="danger" plain @click="openEvents(null)" data-testid="dev-events">{{ t('device.events') }}</el-button>
      <el-button type="warning" plain :loading="syncing" @click="syncDevices">{{ t('device.sync') }}</el-button>
      <el-button plain :loading="statusSyncing" @click="syncStatus">{{ t('device.syncStatus') }}</el-button>
      <el-button type="warning" plain data-testid="device-import"
                 @click="openImport">{{ t('device.import') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="t('misc2.deviceTip')"
              style="margin-bottom:12px" />

    <el-alert v-if="fresh && fresh.stale > 0" type="warning" :closable="false" show-icon
              style="margin-bottom:10px"
              :title="t('misc4.freshness', { fresh: fresh.fresh, total: fresh.total, stale: fresh.stale, rate: fresh.staleRate })">
      <template #default>
        <el-button link type="primary" @click="freshVisible = true">{{ t('device.silent') }}</el-button>
      </template>
    </el-alert>

    <el-table :empty-text="t('misc2.deviceEmpty')" :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="deviceId" :label="t('device.id')" width="200">
        <template #default="{ row }">{{ row.deviceIdName || row.deviceId }}</template>
      </el-table-column>
      <el-table-column prop="deviceName" :label="t('device.name')" min-width="150" />
      <el-table-column prop="deviceType" :label="t('device.typeCol')" width="120">
        <template #default="{ row }">{{ row.deviceTypeLabel || enumLabel('deviceType', row.deviceType) }}</template>
      </el-table-column>
      <el-table-column prop="deviceMac" :label="t('device.mac')" width="160" />
      <el-table-column :label="t('device.org')" width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>
      </el-table-column>
      <el-table-column prop="spaceId" :label="t('device.space')" width="140">
        <template #default="{ row }">{{ row.spaceIdName || row.spaceId }}</template>
      </el-table-column>
      <el-table-column prop="onlineStatus" :label="t('device.onlineCol')" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.onlineStatus === 1 ? 'success' : 'info'">
            {{ row.onlineStatus === 1 ? t('misc2.online') : t('misc2.offline') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="battery" :label="t('device.battery')" width="90">
        <template #default="{ row }">
          <span v-if="row.battery != null && row.battery < 20"
                style="color:#f56c6c">{{ row.battery }}%</span>
          <span v-else>{{ row.battery ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="deviceStatus" :label="t('device.status')" width="110">
        <template #default="{ row }">{{ row.deviceStatusLabel || enumLabel('deviceStatus', row.deviceStatus) }}</template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('device.detail')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>

    <!-- 设备告警 / 事件 -->
    <el-dialog v-model="evVisible" :title="t('device.eventTitle')" width="900px" top="6vh">
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <el-select v-model="evQuery.identifier" :placeholder="t('device.eventType')" clearable
                   style="width:200px" @change="loadEvents">
          <el-option v-for="t in evTypes" :key="t.code" :value="t.code"
                     :label="t.label + (t.level === 'CRITICAL' ? '（严重）' : '')" />
        </el-select>
        <el-checkbox v-model="evQuery.alarmOnly" @change="loadEvents">{{ t('misc2.alarmOnly') }}</el-checkbox>
        <el-checkbox v-model="evQuery.unhandledOnly" @change="loadEvents">{{ t('misc4.unhandledOnly') }}</el-checkbox>
        <span class="muted" style="font-size:12px">
          {{ t('misc4.eventStats', { total: evTotal, unhandled: evStats.unhandled || 0 }) }}
        </span>
      </div>
      <el-table :data="evRows" v-loading="evLoading" size="small" border max-height="420">
        <el-table-column prop="eventTime" :label="t('device.time')" width="170" />
        <el-table-column prop="deviceId" :label="t('device.device')" width="170" />
        <el-table-column prop="identifier" :label="t('device.typeCol')" width="150">
          <template #default="{ row }">{{ evLabel(row.identifier) }}</template>
        </el-table-column>
        <el-table-column prop="eventLevel" :label="t('device.level')" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="levelTagType(row.eventLevel)">
              {{ levelLabel(row.eventLevel) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="body" :label="t('device.body')" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ fmtEventBody(row.body) }}</template>
        </el-table-column>
        <el-table-column prop="handled" :label="t('device.handled')" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.handled ? 'success' : 'danger'">
              {{ row.handled ? t('misc4.handled') : t('misc4.unhandled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('device.actions')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="!row.handled" link type="primary"
                       @click="handleEvent(row)">标记处理</el-button>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:10px" layout="total, prev, pager, next"
                     :total="+evTotal || 0" :page-size="evQuery.pageSize"
                     :current-page="evQuery.pageNum"
                     @current-change="(p) => { evQuery.pageNum = p; loadEvents() }" />
    </el-dialog>

    <!-- 静默设备 -->
    <el-dialog v-model="freshVisible" :title="t('device.silentTitle')" width="760px">
      <el-alert type="info" :closable="false" show-icon
                title="按静默时长倒序；长时间静默可能是离线、网关故障或未接入。" />
      <el-table :data="(fresh && fresh.staleDevices) || []" size="small" border
                max-height="380" style="margin-top:10px">
        <el-table-column prop="deviceId" :label="t('device.deviceNo')" width="170" />
        <el-table-column prop="deviceName" :label="t('device.name')" min-width="140" />
        <el-table-column prop="deviceType" :label="t('device.typeCol')" width="110" />
        <el-table-column prop="hoursSilent" :label="t('device.hoursSilent')" width="110" />
        <el-table-column prop="lastReportTime" :label="t('device.lastReport')" width="170" />
        <el-table-column prop="battery" :label="t('device.battery')" width="80" />
      </el-table>
    </el-dialog>

    <!-- 设备批量导入 -->
    <el-dialog v-model="impVisible" :title="t('misc4.importTitle')" width="820px" @close="resetImport">
      <el-steps :active="impStep" simple style="margin-bottom:14px">
        <el-step title="选择文件" />
        <el-step title="校验预览" />
        <el-step title="导入结果" />
      </el-steps>

      <div v-if="impStep === 1">
        <el-alert type="info" :closable="false" show-icon
                  title="CSV 列：设备编号, 设备名称, 设备类型, 设备MAC, 房源编号(可空)" />
        <div class="muted" style="font-size:12px;margin:8px 0">
          设备类型可填：门锁 / 门禁 / 道闸 / 摄像头 / 电表 / 水表 / 燃气表 / 传感器（也支持英文码）
        </div>
        <div style="margin:12px 0;display:flex;gap:8px;align-items:center">
          <el-button size="small" @click="downloadDeviceTemplate">下载模板</el-button>
          <span class="muted" style="font-size:12px">设备编号重复会自动跳过</span>
        </div>
        <el-upload :auto-upload="false" :limit="1" accept=".csv"
                   :on-change="onImportFile" :file-list="impFiles">
          <el-button type="primary" plain>选择 CSV 文件</el-button>
        </el-upload>
      </div>

      <div v-else-if="impStep === 2">
        <el-alert :type="impProblems.length ? 'warning' : 'success'" :closable="false" show-icon
                  :title="impProblems.length
                    ? ('预览发现 ' + impProblems.length + ' 处问题，可修正后重新选择')
                    : ('准备导入 ' + impRows.length + ' 行')" />
        <el-table :data="impRows.slice(0, 8)" size="small" border max-height="240"
                  style="margin-top:8px">
          <el-table-column prop="line" label="行" width="60" />
          <el-table-column prop="deviceId" label="设备编号" width="170" />
          <el-table-column prop="deviceName" label="设备名称" min-width="140" />
          <el-table-column prop="typeLabel" label="类型" width="100" />
          <el-table-column prop="mac" label="MAC" width="160" />
          <el-table-column prop="houseCode" label="房源编号" width="140" />
        </el-table>
        <el-table v-if="impProblems.length" :data="impProblems" size="small" border
                  style="margin-top:8px" max-height="140">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="问题" />
        </el-table>
      </div>

      <div v-else>
        <el-alert :type="impResult && impResult.errors && impResult.errors.length ? 'warning' : 'success'"
                  :closable="false" show-icon
                  :title="impResult
                    ? ('共 ' + impResult.total + ' 行，成功 ' + impResult.created
                       + '，跳过 ' + impResult.skipped)
                    : '导入完成'" />
        <div style="margin:10px 0">
          <el-button size="small"
                     :disabled="!impResult || !impResult.errors || !impResult.errors.length"
                     @click="exportImpErrors">导出失败行</el-button>
        </div>
        <el-table v-if="impResult && impResult.errors" :data="impResult.errors"
                  size="small" border max-height="220">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="原因" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="impVisible = false">关闭</el-button>
        <el-button v-if="impStep === 2" @click="impStep = 1">重新选择</el-button>
        <el-button v-if="impStep === 3" @click="load">刷新列表</el-button>
        <el-button v-if="impStep === 2" type="primary" :loading="impSaving"
                   :disabled="!impFile || !!impProblems.length" @click="doImport">
          开始导入
        </el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import { enumLabel } from '@/constants/enums'
import { levelLabel, levelTagType, fmtEventBody } from '@/utils/eventDisplay'
import { ref, reactive, onMounted } from 'vue'
import req from '@/api/request'
import SpaceSelect from '@/components/SpaceSelect.vue'
import DetailView from '@/components/DetailView.vue'
import { devApi } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const stats = ref({})
const syncing = ref(false)
const query = reactive({ pageNum: 1, pageSize: 20, spaceId: '', onlineStatus: '',
  deviceType: '' })

const devTypes = ref([])

async function loadTypes() {
  try {
    const list = await req.get('/devices/types')
    devTypes.value = (list || []).filter((t) => t.count > 0 || t.code !== 'OTHER')
  } catch (e) { devTypes.value = [] }
}

async function load() {
  loading.value = true
  try {
    const data = await devApi.devices({
      pageNum: query.pageNum, pageSize: query.pageSize,
      spaceId: query.spaceId || undefined,
      deviceType: query.deviceType || undefined,
      onlineStatus: query.onlineStatus === '' ? undefined : query.onlineStatus
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
    stats.value = await devApi.deviceStats()
  } catch (e) { rows.value = [] } finally { loading.value = false }
}

const query0 = JSON.parse(JSON.stringify(query))
async function syncDevices() {
  syncing.value = true
  try {
    const r = await req.post('/iot/devices/sync?days=1')
    ElMessage.success('已同步：拉取 ' + r.fetched + '，新增 ' + r.created
      + '，更新 ' + r.updated)
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '同步失败')
  } finally { syncing.value = false }
}

function resetQuery() {
  Object.assign(query, query0)
  load()
}


/** 设备告警与事件 */
const statusSyncing = ref(false)

/** 拉取一批设备的在线/电量状态（IoT 批量状态接口） */
async function syncStatus() {
  statusSyncing.value = true
  try {
    const r = await req.post('/iot/devices/status-sync', null, { params: { limit: 200 } })
    ElMessage.success('状态已同步：更新 ' + (r?.updated || 0) + ' 台（在线 ' + (r?.online || 0) + '）')
    load(); loadFreshness()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '状态同步失败')
  } finally { statusSyncing.value = false }
}

const fresh = ref(null)
const freshVisible = ref(false)

async function loadFreshness() {
  try {
    fresh.value = await req.get('/devices/freshness', { params: { hours: 24 } })
  } catch (e) { fresh.value = null }
}

const impVisible = ref(false)
const impStep = ref(1)
const impSaving = ref(false)
const impFiles = ref([])
const impRows = ref([])
const impProblems = ref([])
const impResult = ref(null)
let impFile = null

const DEVICE_TYPE_LABEL = {
  LOCK: '门锁', ACCESS: '门禁', BARRIER: '道闸', CAMERA: '摄像头',
  ELEC_METER: '电表', WATER_METER: '水表', GAS_METER: '燃气表', SENSOR: '传感器'
}
const TYPE_BY_TEXT = {
  门锁: 'LOCK', 智能锁: 'LOCK', 门禁: 'ACCESS', 道闸: 'BARRIER', 摄像头: 'CAMERA',
  视频: 'CAMERA', 电表: 'ELEC_METER', 水表: 'WATER_METER', 燃气表: 'GAS_METER',
  气表: 'GAS_METER', 传感器: 'SENSOR'
}

function openImport() {
  resetImport()
  impVisible.value = true
}

function resetImport() {
  impStep.value = 1
  impFiles.value = []
  impRows.value = []
  impProblems.value = []
  impResult.value = null
  impSaving.value = false
  impFile = null
}

function downloadDeviceTemplate() {
  const csv = '\ufeff设备编号,设备名称,设备类型,设备MAC,房源编号\n'
    + 'LK00000001,1栋101门锁,门锁,AA:BB:CC:DD:EE:01,H8063501\n'
    + 'EM00000001,1栋101电表,电表,AA:BB:CC:DD:EE:02,\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备导入模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

/** 简单 CSV 解析（支持引号） */
function parseCsvText(text) {
  const clean = text.replace(/^\ufeff/, '')
  const rows = []
  let cur = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < clean.length; i++) {
    const ch = clean[i]
    if (quoted) {
      if (ch === '"' && clean[i + 1] === '"') { cell += '"'; i++ }
      else if (ch === '"') quoted = false
      else cell += ch
    } else if (ch === '"') quoted = true
    else if (ch === ',') { cur.push(cell); cell = '' }
    else if (ch === '\n') { cur.push(cell); rows.push(cur); cur = []; cell = '' }
    else if (ch !== '\r') cell += ch
  }
  if (cell !== '' || cur.length) { cur.push(cell); rows.push(cur) }
  return rows.filter((r) => r.some((x) => (x || '').trim() !== ''))
}

function onImportFile(file) {
  impFile = file.raw
  impFiles.value = [file]
  impResult.value = null
  const reader = new FileReader()
  reader.onload = (e) => {
    const all = parseCsvText(String(e.target.result || ''))
    if (!all.length) {
      impProblems.value = [{ line: 0, message: '文件为空' }]
      impStep.value = 2
      return
    }
    let body = all
    if (/设备编号|deviceId/i.test(all[0].join(','))) body = all.slice(1)
    const seen = new Set()
    const problems = []
    impRows.value = body.map((cells, i) => {
      const line = i + (all.length - body.length) + 1
      const deviceId = (cells[0] || '').trim()
      const deviceName = (cells[1] || '').trim()
      const typeText = (cells[2] || '').trim()
      const mac = (cells[3] || '').trim()
      const houseCode = (cells[4] || '').trim()
      const code = TYPE_BY_TEXT[typeText] || (DEVICE_TYPE_LABEL[typeText] ? typeText : null)
      if (!deviceId) problems.push({ line, message: '设备编号为空' })
      else if (seen.has(deviceId)) problems.push({ line, message: '文件内设备编号重复：' + deviceId })
      else seen.add(deviceId)
      if (!typeText) problems.push({ line, message: '设备类型为空' })
      else if (!code) problems.push({ line, message: '无法识别的设备类型：' + typeText })
      return {
        line, deviceId, deviceName, mac, houseCode,
        typeLabel: code ? DEVICE_TYPE_LABEL[code] : typeText
      }
    })
    impProblems.value = problems
    impStep.value = 2
  }
  reader.readAsText(file.raw, 'utf-8')
}

async function doImport() {
  if (!impFile) { ElMessage.warning('请选择 CSV 文件'); return }
  impSaving.value = true
  try {
    const fd = new FormData()
    fd.append('file', impFile)
    const r = await req.post('/devices/import', fd,
      { headers: { 'Content-Type': 'multipart/form-data' } })
    impResult.value = r || {}
    impStep.value = 3
    ElMessage.success('导入完成：成功 ' + (r?.created || 0) + '，跳过 ' + (r?.skipped || 0))
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导入失败')
  } finally { impSaving.value = false }
}

function exportImpErrors() {
  const rows = (impResult.value && impResult.value.errors) || []
  const csv = '\ufeff行号,原因\n'
    + rows.map((x) => x.line + ',' + String(x.message || '').replace(/,/g, '，')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备导入失败行.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

const evVisible = ref(false)
const evLoading = ref(false)
const evRows = ref([])
const evTotal = ref(0)
const evStats = ref({})
const evTypes = ref([])
const evQuery = reactive({ pageNum: 1, pageSize: 20, identifier: '', alarmOnly: true,
  unhandledOnly: false })

const EV_LABEL = {
  OPEN: '开锁', ONLINE: '上线', OFFLINE: '离线', LOW_BATTERY: '低电量告警',
  BATTERY_RESTORED: '低电解除', TAMPER: '防拆告警', TRIAL_ERROR: '试错告警',
  DURESS: '胁迫告警', POWER_OVER: '超功率告警', LOCAL_SWITCH: '本地合闸',
  METER_READ: '抄表读数', OTHER: '其他'
}
function evLabel(code) { return EV_LABEL[code] || code }

async function openEvents() {
  evVisible.value = true
  await loadEvents()
}

async function loadEvents() {
  evLoading.value = true
  try {
    const params = { pageNum: evQuery.pageNum, pageSize: evQuery.pageSize }
    if (evQuery.identifier) params.identifier = evQuery.identifier
    if (evQuery.alarmOnly) params.alarmOnly = true
    const r = await req.get('/dev-events', { params })
    evRows.value = (r && r.rows) || []
    evTotal.value = (r && r.total) || 0
    const st = await req.get('/dev-events/stats',
      { params: evQuery.unhandledOnly ? { unhandledOnly: true } : {} })
    evStats.value = st || {}
    evTypes.value = (st && st.alarmTypes) || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载设备事件失败')
  } finally { evLoading.value = false }
}

async function handleEvent(row) {
  try {
    await req.post(`/dev-events/${row.id}/handle`, { remark: '人工确认处理' })
    ElMessage.success('已标记处理')
    loadEvents()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

onMounted(() => { loadTypes(); load(); loadFreshness() })
</script>
