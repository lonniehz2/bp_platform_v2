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

      <el-pagination
        v-model:current-page="pageNum"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[20, 50, 100, 200]"
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top:12px;justify-content:flex-end"
        data-testid="report-pager"
        @current-change="onQuery"
        @size-change="onSizeChange"
      />
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">导出任务</h4>
      <el-table :data="tasks" border size="small">
        <el-table-column prop="taskNo" label="任务号" width="160" />
        <el-table-column prop="fileName" label="文件名" min-width="200" />
        <el-table-column prop="rowCount" label="行数" width="80" />
        <el-table-column prop="taskStatus" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.taskStatus === 'SUCCESS' ? 'success' : 'info'">
              {{ row.taskStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fileUrl" label="文件路径（服务器）" min-width="240"
                         show-overflow-tooltip />
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览内容</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="previewVisible"
               :title="`导出文件内容（${previewText.length.toLocaleString('zh-CN')} 字符）`"
               width="820px">
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

/** 报表结果分页：此前固定 pageNum=1/pageSize=100，只能看到第一页 */
const pageNum = ref(1)
const pageSize = ref(50)
const total = ref(0)

async function loadReports() {
  reports.value = await rptApi.reports()
}

async function onQuery() {
  if (!reportCode.value) return
  loading.value = true
  try {
    const data = await rptApi.query({
      reportCode: reportCode.value,
      pageNum: pageNum.value,
      pageSize: pageSize.value
    })
    columns.value = data.columns || []
    rows.value = data.rows || []
    total.value = Number(data.total || data.rowCount || rows.value.length || 0)
    summary.value = data.summary || ''
  } finally {
    loading.value = false
  }
}

/** 每页条数变化后回到第 1 页 */
function onSizeChange() {
  pageNum.value = 1
  onQuery()
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
