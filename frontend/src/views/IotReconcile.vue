<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">IoT 日对账</h3>
      <el-tag size="small" type="info">指令 / 回调 / 表计</el-tag>
      <div class="spacer" />
      <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD"
                      style="width:160px" @change="load" />
      <el-button type="primary" :loading="loading" @click="load">对账</el-button>
      <el-button @click="exportCsv">导出 CSV</el-button>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="8">
        <el-card shadow="never">
          <div class="muted">指令成功率</div>
          <div class="num">{{ d.commands?.successRate ?? 0 }}%</div>
          <div class="muted">共 {{ d.commands?.total ?? 0 }} 条 ｜ 未回执 {{ d.commands?.unackedCount ?? 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="muted">回调成功率</div>
          <div class="num">{{ d.callbacks?.successRate ?? 0 }}%</div>
          <div class="muted">已处理 {{ d.callbacks?.done ?? 0 }} / 共 {{ d.callbacks?.total ?? 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never">
          <div class="muted">表计上报覆盖率</div>
          <div class="num">{{ d.meters?.coverageRate ?? 0 }}%</div>
          <div class="muted">已报 {{ d.meters?.covered ?? 0 }} / 应报 {{ d.meters?.expected ?? 0 }}
            ｜ 缺失 {{ d.meters?.missingCount ?? 0 }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12">
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">指令状态分布</div>
          <el-table :data="cmdRows" border size="small">
            <el-table-column prop="name" label="状态" />
            <el-table-column prop="value" label="数量" width="90" align="right" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">回调矩阵（动作 × 状态）</div>
          <el-table :data="cbRows" border size="small">
            <el-table-column prop="action" label="动作" width="140" />
            <el-table-column prop="done" label="已处理" width="90" align="right" />
            <el-table-column prop="failed" label="失败" width="80" align="right" />
            <el-table-column prop="rejected" label="拒绝" width="80" align="right" />
            <el-table-column prop="duplicate" label="重复" width="80" align="right" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="12" style="margin-top:12px">
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">未回执指令（超过 10 分钟）</div>
          <el-table :data="d.commands?.unacked || []" border size="small" max-height="320"
                    empty-text="无未回执指令">
            <el-table-column prop="commandNo" label="指令号" width="180" />
            <el-table-column prop="commandType" label="类型" width="130" />
            <el-table-column prop="deviceId" label="设备" width="150" />
            <el-table-column prop="dispatchTime" label="下发时间" min-width="160" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <div class="card-title">表计未上报（前 50）</div>
          <el-table :data="d.meters?.missing || []" border size="small" max-height="320"
                    empty-text="全部已上报">
            <el-table-column prop="deviceId" label="表号" width="180" />
            <el-table-column prop="deviceType" label="类型" width="130" />
            <el-table-column prop="spaceId" label="空间" min-width="180" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <div class="muted" style="margin-top:10px">
      对账日期：{{ d.date || date }} ｜ 生成时间：{{ d.generatedAt || '—' }}
    </div>
  </div>
</template>

<script setup>
/**
 * IoT 日对账：指令执行、回调处理、表计上报覆盖。
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'

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
