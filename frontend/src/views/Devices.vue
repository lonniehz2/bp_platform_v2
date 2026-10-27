<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">设备管理</h3>
      <el-tag size="small" type="info">
        在线 {{ stats.online ?? 0 }} / 共 {{ stats.total ?? 0 }}
        （{{ stats.onlineRate ?? 0 }}%）
      </el-tag>
      <div class="spacer" />
      <SpaceSelect v-model="query.spaceId" width="210px" testid="spaceselect" />
      <el-select v-model="query.deviceType" placeholder="设备类型" clearable
                 style="width:150px" @change="load">
        <el-option v-for="t in devTypes" :key="t.code" :value="t.code"
                   :label="t.label + (t.count ? '（' + t.count + '）' : '')" />
      </el-select>
      <el-select v-model="query.onlineStatus" placeholder="在线状态" clearable
                 style="width:130px" @change="load">
        <el-option label="在线" :value="1" />
        <el-option label="离线" :value="0" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="danger" plain @click="openEvents(null)" data-testid="dev-events">
        设备告警
      </el-button>
      <el-button type="warning" plain :loading="syncing" @click="syncDevices">
        同步设备
      </el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              title="设备表按空间关联（无 houseId/lockId 列）；门锁与房源关系由绑定记录推导"
              style="margin-bottom:12px" />

    <el-table empty-text="暂无设备，可点「同步设备」从 IoT 拉取" :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="deviceId" label="设备ID" width="200">
        <template #default="{ row }">{{ row.deviceIdName || row.deviceId }}</template>
      </el-table-column>
      <el-table-column prop="deviceName" label="设备名称" min-width="150" />
      <el-table-column prop="deviceType" label="类型" width="120">
        <template #default="{ row }">{{ row.deviceTypeLabel || enumLabel('deviceType', row.deviceType) }}</template>
      </el-table-column>
      <el-table-column prop="deviceMac" label="MAC" width="160" />
      <el-table-column label="组织" width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>
      </el-table-column>
      <el-table-column prop="spaceId" label="空间" width="140">
        <template #default="{ row }">{{ row.spaceIdName || row.spaceId }}</template>
      </el-table-column>
      <el-table-column prop="onlineStatus" label="在线" width="90">
        <template #default="{ row }">
          <el-tag size="small" :type="row.onlineStatus === 1 ? 'success' : 'info'">
            {{ row.onlineStatus === 1 ? '在线' : '离线' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="battery" label="电量" width="90">
        <template #default="{ row }">
          <span v-if="row.battery != null && row.battery < 20"
                style="color:#f56c6c">{{ row.battery }}%</span>
          <span v-else>{{ row.battery ?? '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="deviceStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.deviceStatusLabel || enumLabel('deviceStatus', row.deviceStatus) }}</template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>

    <!-- 设备告警 / 事件 -->
    <el-dialog v-model="evVisible" title="设备告警与事件" width="900px" top="6vh">
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <el-select v-model="evQuery.identifier" placeholder="事件类型" clearable
                   style="width:200px" @change="loadEvents">
          <el-option v-for="t in evTypes" :key="t.code" :value="t.code"
                     :label="t.label + (t.level === 'CRITICAL' ? '（严重）' : '')" />
        </el-select>
        <el-checkbox v-model="evQuery.alarmOnly" @change="loadEvents">只看告警</el-checkbox>
        <el-checkbox v-model="evQuery.unhandledOnly" @change="loadEvents">只看未处理</el-checkbox>
        <span class="muted" style="font-size:12px">
          共 {{ evTotal }} 条，未处理 {{ evStats.unhandled || 0 }} 条
        </span>
      </div>
      <el-table :data="evRows" v-loading="evLoading" size="small" border max-height="420">
        <el-table-column prop="eventTime" label="时间" width="170" />
        <el-table-column prop="deviceId" label="设备" width="170" />
        <el-table-column prop="identifier" label="类型" width="150">
          <template #default="{ row }">{{ evLabel(row.identifier) }}</template>
        </el-table-column>
        <el-table-column prop="eventLevel" label="级别" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="levelTagType(row.eventLevel)">
              {{ levelLabel(row.eventLevel) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="body" label="详情" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ fmtEventBody(row.body) }}</template>
        </el-table-column>
        <el-table-column prop="handled" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.handled ? 'success' : 'danger'">
              {{ row.handled ? '已处理' : '未处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="!row.handled" link type="primary"
                       @click="handleEvent(row)">标记处理</el-button>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:10px" layout="total, prev, pager, next"
                     :total="evTotal" :page-size="evQuery.pageSize"
                     :current-page="evQuery.pageNum"
                     @current-change="(p) => { evQuery.pageNum = p; loadEvents() }" />
    </el-dialog>
</template>

<script setup>
/** 通用详情弹窗（复用 DetailView） */
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

onMounted(() => { loadTypes(); load() })
</script>
