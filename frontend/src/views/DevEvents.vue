<template>
  <div>
    <div class="toolbar">
      <el-select v-model="query.identifier" :placeholder="t('devEvent.eventType')" clearable
                 style="width:200px" @change="load">
        <el-option v-for="t in types" :key="t.code" :value="t.code"
                   :label="t.label + (t.level === 'CRITICAL' ? '（严重）' : '')" />
      </el-select>
      <el-select v-model="query.eventLevel" :placeholder="t('devEvent.level')" clearable
                 style="width:120px" @change="load">
        <el-option :label="t('devEvent.critical')" value="CRITICAL" />
        <el-option :label="t('devEvent.warn')" value="WARN" />
        <el-option :label="t('devEvent.info')" value="INFO" />
      </el-select>
      <DeviceSelect v-model="query.deviceId" width="240px" testid="device-select" />
      <el-checkbox v-model="query.alarmOnly" @change="load">{{ t('miscPage.alarmOnly') }}</el-checkbox>
      <el-checkbox v-model="query.unhandledOnly" @change="load">{{ t('miscPage.unhandledOnly') }}</el-checkbox>
      <el-button type="primary" @click="load">{{ t('devEvent.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('devEvent.reset') }}</el-button>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="6">
        <el-card shadow="never"><div class="muted">{{ t('miscPage.eventTotal') }}</div>
          <div style="font-size:22px;font-weight:600">{{ stats.total || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never"><div class="muted">{{ t('miscPage.eventUnhandled') }}</div>
          <div style="font-size:22px;font-weight:600;color:#f56c6c">{{ stats.unhandled || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never"><div class="muted">{{ t('miscPage.eventCritical') }}</div>
          <div style="font-size:22px;font-weight:600;color:#f56c6c">{{ criticalCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <el-tooltip placement="bottom">
            <template #content>
              {{ t('miscPage.eventTypes', { n: (stats.alarmTypes || []).length }) }}:<br />
              <span v-for="t in stats.alarmTypes || []" :key="t.code">
                {{ t.label }}<br />
              </span>
            </template>
            <div class="muted">{{ t('miscPage.currentAlarmTypes') }}</div>
          </el-tooltip>
          <div style="font-size:22px;font-weight:600">
            {{ stats.typeCount || 0 }}
            <span class="muted" style="font-size:12px;font-weight:400">
              / 系统支持 {{ (stats.alarmTypes || []).length }} 种
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-table :empty-text="t('miscPage.noEvents')" :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="eventTime" :label="t('devEvent.time')" width="170" />
      <el-table-column prop="deviceId" :label="t('devEvent.device')" width="170" />
      <el-table-column prop="identifier" :label="t('devEvent.type')" width="170">
        <template #default="{ row }">{{ labelOf(row.identifier) }}</template>
      </el-table-column>
      <el-table-column prop="eventLevel" :label="t('devEvent.level')" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.eventLevel === 'CRITICAL' ? 'danger'
            : (row.eventLevel === 'WARN' ? 'warning' : 'info')">
            {{ levelLabel(row.eventLevel) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="body" :label="t('devEvent.details')" min-width="260" show-overflow-tooltip>
        <template #default="{ row }">{{ fmtBody(row.body) }}</template>
      </el-table-column>
      <el-table-column prop="handled" :label="t('devEvent.handled')" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.handled ? 'success' : 'danger'">
            {{ row.handled ? t('miscPage.handled') : t('miscPage.unhandled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="handleRemark" :label="t('devEvent.remark')" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.handleRemark || '—' }}</template>
      </el-table-column>
      <el-table-column :label="t('devEvent.actions')" width="110" fixed="right">
        <template #default="{ row }">
          <el-button v-if="!row.handled" link type="primary"
                     @click="handle(row)" data-testid="ev-handle">{{ t('miscPage.markHandled') }}</el-button>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * 设备告警与事件。
 *
 * 承载低电量、防拆、试错、胁迫、超功率、离线等告警，
 * 以及开锁、上下线等记录类事件（IoT 上报）。
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import DeviceSelect from '@/components/DeviceSelect.vue'

const { t } = useI18n()
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const stats = ref({})
const types = ref([])
const query = reactive({ pageNum: 1, pageSize: 20, identifier: '', eventLevel: '',
  deviceId: '', alarmOnly: true, unhandledOnly: false })

const EV_LABEL = {
  OPEN: '开锁', ONLINE: '上线', OFFLINE: '离线', LOW_BATTERY: '低电量告警',
  BATTERY_RESTORED: '低电解除', TAMPER: '防拆告警', TRIAL_ERROR: '试错告警',
  DURESS: '胁迫告警', POWER_OVER: '超功率告警', LOCAL_SWITCH: '本地合闸',
  METER_READ: '抄表读数', OTHER: '其他'
}
const LEVEL_LABEL = { INFO: '信息', WARN: '警告', CRITICAL: '严重' }

function labelOf(code) { return EV_LABEL[code] || code }

/** 事件 body 是 JSON 字符串，这里转成「中文键：值」便于阅读 */
const BODY_KEY_LABEL = {
  pwdId: '密码/卡号', passwordId: '密码/卡号', cardId: '卡号', userId: '用户',
  reason: '原因', count: '次数', battery: '电量(%)', voltage: '电压(V)',
  power: '功率(W)', current: '电流(A)', method: '开锁方式', type: '类型',
  deviceId: '设备', firmware: '固件版本', timestamp: '上报时间', status: '状态',
  lockId: '门锁', mode: '模式', source: '来源', message: '消息'
}
function fmtBody(body) {
  if (!body) return '—'
  const t = String(body).trim()
  if (!t.startsWith('{') && !t.startsWith('[')) return t
  try {
    const o = JSON.parse(t)
    if (Array.isArray(o)) return o.map((x) => fmtBody(JSON.stringify(x))).join('；')
    return Object.entries(o).map(([k, v]) => {
      const key = BODY_KEY_LABEL[k] || k
      const val = (v !== null && typeof v === 'object')
        ? JSON.stringify(v) : String(v)
      return key + '：' + val
    }).join('；')
  } catch (e) {
    return t
  }
}
function levelLabel(code) { return LEVEL_LABEL[code] || code }

const criticalCount = computed(() => {
  const byLevel = stats.value.byLevel || {}
  return byLevel.CRITICAL || 0
})

async function load() {
  loading.value = true
  try {
    const params = { pageNum: query.pageNum, pageSize: query.pageSize }
    if (query.identifier) params.identifier = query.identifier
    if (query.eventLevel) params.eventLevel = query.eventLevel
    if (query.deviceId) params.deviceId = query.deviceId
    if (query.alarmOnly) params.alarmOnly = true
    if (query.unhandledOnly) params.handled = 0
    const r = await req.get('/dev-events', { params })
    rows.value = (r && r.rows) || []
    total.value = (r && r.total) || 0
    // 统计与列表用同一组筛选条件，避免「列表 4 条、卡片 5 条」的口径不一致
    const st = await req.get('/dev-events/stats', { params })

    stats.value = st || {}
    types.value = (st && st.alarmTypes) || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载设备事件失败')
  } finally { loading.value = false }
}

function resetQuery() {
  Object.assign(query, { pageNum: 1, identifier: '', eventLevel: '', deviceId: '',
    alarmOnly: true, unhandledOnly: false })
  load()
}

async function handle(row) {
  try {
    const { value } = await ElMessageBox.prompt('处理说明', '标记已处理', {
      inputValue: '现场确认处理', inputPattern: /\S+/, inputErrorMessage: '请填写说明'
    })
    await req.post(`/dev-events/${row.id}/handle`, { remark: value })
    ElMessage.success('已标记处理')
    load()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e?.response?.data?.message || '操作失败')
    }
  }
}

onMounted(load)
</script>
