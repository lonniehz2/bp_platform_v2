<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="reportCode" placeholder="选择报表" style="width:220px"
                   @change="onQuery">
          <el-option v-for="r in reports" :key="r.reportCode"
                     :label="r.reportName" :value="r.reportCode" />
        </el-select>
        <el-button type="primary" @click="onQuery">查询</el-button>
        <el-button @click="resetQuery">清空</el-button>
        <div class="spacer" />
        <el-button type="success" :loading="exporting" @click="onExport">
          <el-icon><Download /></el-icon>导出 CSV
        </el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column v-for="c in columns" :key="c.key"
                         :prop="c.key" :label="c.title" show-overflow-tooltip />
        <el-table-column v-if="!columns.length" label="提示">
          <template #default>请选择报表后查询</template>
        </el-table-column>
      </el-table>

      <div class="muted" style="margin-top:10px">{{ summary }}</div>
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">导出任务</h4>
      <el-table :data="tasks" border size="small">
        <el-table-column prop="taskNo" label="任务号" width="180" />
        <el-table-column prop="fileName" label="文件名" min-width="220" />
        <el-table-column prop="rowCount" label="行数" width="90" />
        <el-table-column prop="taskStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.taskStatus === 'SUCCESS' ? 'success' : 'info'">
              {{ row.taskStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览内容</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="previewVisible" title="导出文件内容（前 4000 字符）" width="760px">
      <pre class="csv-preview">{{ previewText }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { rptApi } from '@/api/modules'

const reports = ref([])
const reportCode = ref('HOUSE_LEDGER')
const columns = ref([])
const rows = ref([])
const summary = ref('')
const loading = ref(false)
const exporting = ref(false)

const tasks = ref([])
const previewVisible = ref(false)
const previewText = ref('')

async function loadReports() {
  reports.value = await rptApi.reports()
}

async function onQuery() {
  if (!reportCode.value) return
  loading.value = true
  try {
    const data = await rptApi.query({ reportCode: reportCode.value, pageNum: 1, pageSize: 100 })
    columns.value = data.columns || []
    rows.value = data.rows || []
    summary.value = data.summary || ''
  } finally {
    loading.value = false
  }
}

async function onExport() {
  if (!reportCode.value) return
  exporting.value = true
  try {
    const task = await rptApi.export({ reportCode: reportCode.value })
    ElMessage.success(`导出完成：${task.fileName}（${task.rowCount} 行）`)
    tasks.value.unshift(task)
  } finally {
    exporting.value = false
  }
}

async function preview(row) {
  previewText.value = await rptApi.taskContent(row.id)
  previewVisible.value = true
}

function resetQuery() {
  reportCode.value = ''
  onQuery()
}

onMounted(async () => {
  await loadReports()
  await onQuery()
})
</script>

<style scoped>
.csv-preview {
  max-height: 460px;
  overflow: auto;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre;
}
</style>
