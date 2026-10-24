<template>
  <div>
    <div class="toolbar">
      <el-select v-model="query.identifier" placeholder="事件类型" clearable
                 style="width:200px" @change="load">
        <el-option v-for="t in types" :key="t.code" :value="t.code"
                   :label="t.label + (t.level === 'CRITICAL' ? '（严重）' : '')" />
      </el-select>
      <el-select v-model="query.eventLevel" placeholder="级别" clearable
                 style="width:120px" @change="load">
        <el-option label="严重" value="CRITICAL" />
        <el-option label="警告" value="WARN" />
        <el-option label="信息" value="INFO" />
      </el-select>
      <el-input v-model="query.deviceId" placeholder="设备编号" clearable
                style="width:220px" @keyup.enter="load" />
      <el-checkbox v-model="query.alarmOnly" @change="load">只看告警</el-checkbox>
      <el-checkbox v-model="query.unhandledOnly" @change="load">只看未处理</el-checkbox>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="6">
        <el-card shadow="never"><div class="muted">事件总数</div>
          <div style="font-size:22px;font-weight:600">{{ stats.total || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never"><div class="muted">未处理</div>
          <div style="font-size:22px;font-weight:600;color:#f56c6c">{{ stats.unhandled || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never"><div class="muted">严重</div>
          <div style="font-size:22px;font-weight:600;color:#f56c6c">{{ criticalCount }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never"><div class="muted">告警类型</div>
          <div style="font-size:22px;font-weight:600">{{ (stats.alarmTypes || []).length }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="eventTime" label="时间" width="170" />
      <el-table-column prop="deviceId" label="设备编号" width="170" />
      <el-table-column prop="identifier" label="类型" width="170">
        <template #default="{ row }">{{ labelOf(row.identifier) }}</template>
      </el-table-column>
      <el-table-column prop="eventLevel" label="级别" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.eventLevel === 'CRITICAL' ? 'danger'
            : (row.eventLevel === 'WARN' ? 'warning' : 'info')">
            {{ levelLabel(row.eventLevel) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="body" label="详情" min-width="240" show-overflow-tooltip />
      <el-table-column prop="handled" label="处理状态" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.handled ? 'success' : 'danger'">
            {{ row.handled ? '已处理' : '未处理' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="handleRemark" label="处理说明" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">{{ row.handleRemark || '—' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button v-if="!row.handled" link type="primary"
                     @click="handle(row)" data-testid="ev-handle">标记处理</el-button>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />
  </div>
</template>

<script setup>
/**
 * 设备告警与事件。
 *
 * 承载低电量、防拆、试错、胁迫、超功率、离线等告警，
 * 以及开锁、上下线等记录类事件（IoT 上报）。
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

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
    const st = await req.get('/dev-events/stats',
      { params: query.unhandledOnly ? { unhandledOnly: true } : {} })
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
