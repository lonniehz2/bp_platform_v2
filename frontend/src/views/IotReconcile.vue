<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('iotRec.title') }}</h3>
      <el-tag size="small" type="info">{{ t('iotRec.subtitle') }}</el-tag>
      <div class="spacer" />
      <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD"
                      style="width:160px" @change="load" />
      <el-button type="primary" :loading="loading" @click="load">{{ t('iotRec.load') }}</el-button>
      <el-button @click="exportCsv">{{ t('iotRec.export') }}</el-button>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="8">
        <el-card shadow="never">
          <div class="muted">{{ t('iotRec.cmdSuccess') }}</div>
          <div class="num">{{ d.commands?.successRate ?? 0 }}%</div>
          <div class="muted">{{ t('iotRec.total', { total: d.commands?.total ?? 0, unacked: d.commands?.unackedCount ?? 0 }) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="muted">{{ t('iotRec.callbackSuccess') }}</div>
          <div class="num">{{ d.callbacks?.successRate ?? 0 }}%</div>
          <div class="muted">{{ t('iotRec.doneOf', { done: d.callbacks?.done ?? 0, total: d.callbacks?.total ?? 0 }) }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="muted">{{ t('iotRec.meterCoverage') }}</div>
          <div class="num">{{ d.meters?.coverageRate ?? 0 }}%</div>
          <div class="muted">{{ t('iotRec.covered', { covered: d.meters?.covered ?? 0, expected: d.meters?.expected ?? 0, missing: d.meters?.missingCount ?? 0 }) }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">{{ t('iotRec.cmdStatus') }}</div>
          <el-table :data="cmdRows" border size="small">
            <el-table-column prop="name" :label="t('iotRec.status')" />
            <el-table-column prop="value" :label="t('iotRec.count')" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">{{ t('iotRec.callbackMatrix') }}</div>
          <el-table :data="cbRows" border size="small">
            <el-table-column prop="action" :label="t('iotRec.action')" width="140" />
            <el-table-column prop="done" :label="t('iotRec.done')" width="90" align="right" />
            <el-table-column prop="failed" :label="t('iotRec.failed')" width="80" align="right" />
            <el-table-column prop="rejected" :label="t('iotRec.rejected')" width="80" align="right" />
            <el-table-column prop="duplicate" :label="t('iotRec.duplicate')" width="80" align="right" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" style="margin-top:12px">
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">{{ t('iotRec.unackedTitle') }}</div>
          <el-table :data="d.commands?.unacked || []" border size="small" max-height="320"
                    :empty-text="t('iotRec.unackedEmpty')">
            <el-table-column prop="commandNo" :label="t('iotRec.commandNo')" width="180" />
            <el-table-column prop="commandType" :label="t('iotRec.type')" width="130" />
            <el-table-column prop="deviceId" :label="t('iotRec.device')" width="150" />
            <el-table-column prop="dispatchTime" :label="t('iotRec.dispatchTime')" min-width="160" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">{{ t('iotRec.meterMissing') }}</div>
          <el-table :data="d.meters?.missing || []" border size="small" max-height="320"
                    :empty-text="t('iotRec.meterEmpty')">
            <el-table-column prop="deviceId" :label="t('iotRec.meterNo')" width="180" />
            <el-table-column prop="deviceType" :label="t('iotRec.type')" width="130" />
            <el-table-column prop="spaceId" :label="t('iotRec.space')" min-width="180" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <div class="muted" style="margin-top:10px">
      {{ t('iotRec.date', { date: d.date || date, time: d.generatedAt || '—' }) }}
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * IoT 日对账：指令执行、回调处理、表计上报覆盖。
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'

const { t } = useI18n()
const CMD_LABEL = { PENDING: '待下发', SENT: '已下发', SUCCESS: '成功',
  FAILED: '失败', TIMEOUT: '超时', CANCELED: '已取消' }

const loading = ref(false)
const d = ref({})
const date = ref(new Date().toISOString().slice(0, 10))

const cmdRows = computed(() => {
  const m = d.value.commands?.byStatus || {}
  return Object.keys(m).map((k) => ({ name: CMD_LABEL[k] || k, value: m[k] }))
})

const cbRows = computed(() => {
  const m = d.value.callbacks?.matrix || {}
  return Object.keys(m).map((action) => {
    const row = m[action] || {}
    return { action,
      done: row.DONE || 0,
      failed: row.FAILED || 0,
      rejected: row.REJECTED || 0,
      duplicate: row.DUPLICATE || 0 }
  })
})

async function load() {
  loading.value = true
  try {
    d.value = await req.get('/iot/reconcile', { params: { date: date.value } })
  } catch (e) {
    ElMessage.error('对账加载失败')
  } finally { loading.value = false }
}

function exportCsv() {
  const rows = [['类别', '项目', '数值']]
  rows.push(['指令', '总数', d.value.commands?.total ?? 0])
  rows.push(['指令', '成功率(%)', d.value.commands?.successRate ?? 0])
  rows.push(['指令', '未回执', d.value.commands?.unackedCount ?? 0])
  cmdRows.value.forEach((r) => rows.push(['指令状态', r.name, r.value]))
  rows.push(['回调', '总数', d.value.callbacks?.total ?? 0])
  rows.push(['回调', '成功率(%)', d.value.callbacks?.successRate ?? 0])
  cbRows.value.forEach((r) => rows.push(['回调动作', r.action,
    'DONE=' + r.done + ' FAILED=' + r.failed + ' REJECTED=' + r.rejected]))
  rows.push(['表计', '应报', d.value.meters?.expected ?? 0])
  rows.push(['表计', '已报', d.value.meters?.covered ?? 0])
  rows.push(['表计', '覆盖率(%)', d.value.meters?.coverageRate ?? 0])
  const csv = rows.map((r) => r.map((c) => '"' + String(c).replace(/"/g, '""') + '"').join(','))
    .join('\r\n')
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'iot-reconcile-' + (d.value.date || date.value) + '.csv'
  document.body.appendChild(a); a.click(); document.body.removeChild(a)
  URL.revokeObjectURL(a.href)
}

onMounted(load)
</script>

<style scoped>
.num { font-size: 26px; font-weight: 600; margin: 4px 0; }
.card-title { font-weight: 600; margin-bottom: 8px; }
</style>
