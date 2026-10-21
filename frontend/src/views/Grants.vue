<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">授权与对账</h3>
        <el-tag size="small" :type="stats.riskLevel === 'HIGH' ? 'danger'
          : (stats.riskLevel === 'MEDIUM' ? 'warning' : 'success')">
          风险 {{ stats.riskLevel || '-' }}
        </el-tag>
        <span class="muted">待处置 {{ stats.pending ?? 0 }} 条</span>
        <div class="spacer" />
        <el-input v-model="lockId" placeholder="门锁ID（可空=全部）"
                  style="width:200px" />
        <el-button type="primary" :loading="running" @click="runReconcile">
          执行对账
        </el-button>
      </div>

      <el-alert type="info" :closable="false" show-icon
                title="LOCAL_MISSING = 本地有效但设备未下发（住户刷不开门）；IOT_EXTRA = 已撤销但设备仍存在（安全风险）"
                style="margin-bottom:12px" />

      <el-table :data="diffs" v-loading="loading" border size="small">
        <el-table-column prop="diffType" label="差异类型" width="150">
          <template #default="{ row }">
            <el-tag size="small" :type="row.diffType === 'IOT_EXTRA' ? 'danger' : 'warning'">
              {{ row.diffTypeLabel || enumLabel('diffType', row.diffType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lockId" label="门锁" width="170">
          <template #default="{ row }">{{ row.lockIdName || row.lockId }}</template>
        </el-table-column>
        <el-table-column prop="personId" label="人员" width="120">
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="localValue" label="本地值" min-width="200"
                         show-overflow-tooltip />
        <el-table-column prop="iotValue" label="IoT 值" min-width="180"
                         show-overflow-tooltip />
        <el-table-column prop="handleStatus" label="处置状态" width="110">
          <template #default="{ row }">{{ row.handleStatusLabel || enumLabel('handleStatus', row.handleStatus) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.diffType === 'LOCAL_MISSING'" link type="primary"
                       :disabled="row.handleStatus !== 'PENDING'"
                       @click="handle(row, 'REGRANT')">重新授权</el-button>
            <el-button v-if="row.diffType === 'IOT_EXTRA'" link type="danger"
                       :disabled="row.handleStatus !== 'PENDING'"
                       @click="handle(row, 'REVOKE')">撤销</el-button>
            <el-button link :disabled="row.handleStatus !== 'PENDING'"
                       @click="handle(row, 'IGNORED')">忽略</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }" />
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">授权审计（只追加，不可改删）</h4>
      <el-table :data="audits" border size="small">
        <el-table-column prop="bizType" label="类型" width="120">
          <template #default="{ row }">{{ row.bizTypeLabel || enumLabel('bizType', row.bizType) }}</template>
        </el-table-column>
        <el-table-column prop="personId" label="人员" width="120">
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="operatorName" label="操作人" width="120" />
        <el-table-column prop="reason" label="原因" min-width="200" />
        <el-table-column prop="result" label="结果" width="100" />
        <el-table-column prop="createTime" label="时间" width="170" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { grantApi } from '@/api/modules'

const loading = ref(false)
const running = ref(false)
const diffs = ref([])
const total = ref(0)
const stats = ref({})
const audits = ref([])
const lockId = ref('')
const query = reactive({ pageNum: 1, pageSize: 20 })

async function load() {
  loading.value = true
  try {
    const d = await grantApi.diffs({ ...query })
    diffs.value = d.rows || []
    total.value = Number(d.total || 0)
    stats.value = await grantApi.reconcileStats()
    const a = await grantApi.auditLogs({ pageNum: 1, pageSize: 10 })
    audits.value = a.rows || []
  } finally { loading.value = false }
}

async function runReconcile() {
  running.value = true
  try {
    const r = await grantApi.reconcileRun(lockId.value || undefined)
    ElMessage.success(`对账完成：差异 ${r.diffRecorded} 条（${r.conclusion}）`)
    load()
  } finally { running.value = false }
}

async function handle(row, action) {
  await grantApi.handleDiff(row.id, { action, remark: '页面处置' })
  ElMessage.success('已处置')
  load()
}

onMounted(load)
</script>
