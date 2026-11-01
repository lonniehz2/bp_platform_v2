<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('iotMon.title') }}</h3>
      <el-tag size="small" type="info">{{ t('iotMon.subtitle') }}</el-tag>
      <div class="spacer" />
      <el-select v-model="hours" style="width:130px" @change="load">
        <el-option :label="t('iotMon.last24')" :value="24" />
        <el-option :label="t('iotMon.last72')" :value="72" />
        <el-option :label="t('iotMon.last7')" :value="168" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="load">{{ t('iotMon.refresh') }}</el-button>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="6">
        <el-card shadow="never">
          <div class="muted">{{ t('iotMon.onlineRate') }}</div>
          <div class="num">{{ m.devices?.onlineRate ?? 0 }}%</div>
          <div class="muted">{{ t('iotMon.onlineOf', { online: m.devices?.online ?? 0, total: m.devices?.total ?? 0 }) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="muted">{{ t('iotMon.cmdSuccess') }}</div>
          <div class="num">{{ m.commands?.successRate ?? 0 }}%</div>
          <div class="muted">{{ t('iotMon.successOf', { success: m.commands?.success ?? 0, total: m.commands?.total ?? 0 }) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="muted">{{ t('iotMon.callbackSuccess') }}</div>
          <div class="num">{{ m.callbacks?.successRate ?? 0 }}%</div>
          <div class="muted">{{ t('iotMon.doneOf', { done: m.callbacks?.done ?? 0, total: m.callbacks?.total ?? 0 }) }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never">
          <div class="muted">{{ t('iotMon.nonce') }}</div>
          <div class="num">{{ m.nonceCount ?? 0 }}</div>
          <div class="muted">{{ t('iotMon.nonceHint') }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" style="margin-top:12px">
      <el-col :span="24">
        <el-card shadow="never">
          <div class="card-title">{{ t('iotMon.latency') }}</div>
          <div style="display:flex;gap:32px;margin-top:6px">
            <div><div class="muted">{{ t('iotMon.avg') }}</div>
              <div class="num">{{ m.commands?.cost?.avgMs ?? '—' }} ms</div></div>
            <div><div class="muted">P95</div>
              <div class="num">{{ m.commands?.cost?.p95Ms ?? '—' }} ms</div></div>
            <div><div class="muted">{{ t('iotMon.max') }}</div>
              <div class="num">{{ m.commands?.cost?.maxMs ?? '—' }} ms</div></div>
            <div><div class="muted">{{ t('iotMon.samples') }}</div>
              <div class="num">{{ m.commands?.cost?.samples ?? 0 }}</div></div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :span="8">
        <el-card shadow="never">
          <div class="card-title">{{ t('iotMon.cmdStatus') }}</div>
          <el-table :data="statusRows(m.commands?.byStatus, CMD_LABEL)" border size="small">
            <el-table-column prop="name" :label="t('iotMon.status')" />
            <el-table-column prop="value" :label="t('iotMon.count')" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="card-title">{{ t('iotMon.callbackActions') }}</div>
          <el-table :data="statusRows(m.callbacks?.byAction, ACTION_LABEL)" border size="small">
            <el-table-column prop="name" :label="t('iotMon.action')" />
            <el-table-column prop="value" :label="t('iotMon.count')" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="card-title">{{ t('iotMon.eventTop', { hours }) }}</div>
          <el-table :data="eventRows" border size="small">
            <el-table-column prop="name" :label="t('iotMon.type')" />
              <el-table-column prop="count" :label="t('iotMon.count')" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <div class="muted" style="margin-top:10px">
      {{ t('iotMon.window', { hours, time: m.generatedAt || '—' }) }}
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * IoT 监控：在线率、指令成功率、回调成功率、事件分布。
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'

const { t } = useI18n()
const hours = ref(24)
const loading = ref(false)
const m = ref({})

const CMD_LABEL = { PENDING: '待下发', SENT: '已下发', SUCCESS: '成功',
  FAILED: '失败', TIMEOUT: '超时', CANCELED: '已取消' }
const ACTION_LABEL = { event: '设备事件', access: '开门记录', 'command/ack': '指令回执',
  'grant/ack': '授权回执', heartbeat: '心跳', meter: '表计读数',
  'device-status': '上下线', 'alarm-ack': '告警恢复' }
const EVENT_LABEL = { OFFLINE: '离线', ONLINE: '上线', LOW_BATTERY: '低电量',
  TAMPER: '防拆', DURESS: '胁迫', TRIAL_ERROR: '试错', POWER_OVER: '超功率',
  BATTERY_RESTORED: '低电解除', LOCAL_SWITCH: '本地合闸', METER_READ: '抄表读数',
  OPEN: '开锁', OTHER: '其他' }

function statusRows(map, labels) {
  if (!map) return []
  return Object.keys(map).map((k) => ({ name: (labels && labels[k]) || k, value: map[k] }))
}

async function load() {
  loading.value = true
  try {
    m.value = await req.get('/iot/metrics', { params: { hours: hours.value } })
  } catch (e) {
    ElMessage.error('监控指标加载失败')
  } finally { loading.value = false }
}

const eventRows = computed(() => ((m.value.events && m.value.events.top) || [])
  .map((x) => ({ name: EVENT_LABEL[x.identifier] || x.identifier, count: x.count })))

onMounted(load)
</script>

<style scoped>
.num { font-size: 26px; font-weight: 600; margin: 4px 0; }
.card-title { font-weight: 600; margin-bottom: 8px; }
</style>
