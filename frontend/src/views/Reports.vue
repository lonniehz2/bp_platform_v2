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
        <el-select v-model="exportFormat" style="width:120px" data-testid="export-format">
          <el-option label="CSV" value="CSV" />
          <el-option label="Excel" value="EXCEL" />
        </el-select>
        <el-button type="success" :loading="exporting" @click="onExport">
          <el-icon><Download /></el-icon>导出
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
      <div class="toolbar" style="margin-bottom:12px">
        <h4 style="margin:0">导出任务</h4>
        <div class="spacer" />
        <el-select v-model="taskStatusFilter" placeholder="状态" clearable
                   style="width:120px" @change="applyTaskFilter">
          <el-option label="待执行" value="PENDING" />
          <el-option label="执行中" value="RUNNING" />
          <el-option label="成功" value="SUCCESS" />
          <el-option label="失败" value="FAILED" />
        </el-select>
        <el-button @click="loadTasks">刷新</el-button>
        <el-button type="warning" :loading="runningPending" @click="runPending">
          补跑待执行
        </el-button>
      </div>
      <el-table :data="filteredTasks" border size="small">
        <el-table-column prop="taskNo" label="任务号" width="160" />
        <el-table-column prop="fileName" label="文件名" min-width="200" />
        <el-table-column prop="rowCount" label="行数" width="80" />
        <el-table-column prop="taskStatus" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.taskStatus === 'SUCCESS' ? 'success' : 'info'">
              {{ row.taskStatusLabel || enumLabel('taskStatus', row.taskStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fileUrl" label="文件路径（服务器）" min-width="240"
                         show-overflow-tooltip />
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览</el-button>
            <el-button link type="success" @click="download(row)">下载</el-button>
            <el-button link @click="showTask(row)">任务详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 任务详情 -->
    <el-dialog v-model="taskDetailVisible" title="导出任务详情" width="620px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="任务号">{{ taskDetail.taskNo }}</el-descriptions-item>
        <el-descriptions-item label="报表">{{ taskDetail.reportCode }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ taskDetail.fileName }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          {{ taskDetail.taskStatusLabel || enumLabel('taskStatus', taskDetail.taskStatus) }}
        </el-descriptions-item>
        <el-descriptions-item label="行数">{{ taskDetail.rowCount }}</el-descriptions-item>
        <el-descriptions-item label="耗时">{{ taskDetail.costMs }} ms</el-descriptions-item>
        <el-descriptions-item label="服务器路径">
          {{ taskDetail.fileUrl || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ taskDetail.createTime || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="失败原因">
          {{ taskDetail.errorMsg || '—' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="taskDetailVisible = false">关闭</el-button>
        <el-button type="success" @click="download(taskDetail)">下载</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewVisible"
               :title="`导出文件内容（${previewText.length.toLocaleString('zh-CN')} 字符）`"
               width="820px">
      <pre class="csv-preview">{{ previewText }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { enumLabel } from '@/constants/enums'
import { ElMessage } from 'element-plus'
import { rptApi } from '@/api/modules'
import req from '@/api/request'

const reports = ref([])
const reportCode = ref('HOUSE_LEDGER')
const columns = ref([])
const rows = ref([])
const summary = ref('')
const loading = ref(false)
const exporting = ref(false)
/** 导出格式：CSV（默认）/ EXCEL */
const exportFormat = ref('CSV')

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
    const task = await rptApi.export({
      reportCode: reportCode.value,
      exportFormat: exportFormat.value
    })
    ElMessage.success(`导出完成：${task.fileName}（${task.rowCount} 行）`)
    tasks.value.unshift(task)
  } finally {
    exporting.value = false
  }
}

/** 下载导出文件（带鉴权，必须走 axios 拿 blob 再触发保存） */
async function download(row) {
  try {
    const blob = await rptApi.downloadTask(row.id)
    const url = window.URL.createObjectURL(new Blob([blob]))
    const a = document.createElement('a')
    a.href = url
    a.download = row.fileName || 'report.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (e) {
    ElMessage.error('下载失败，请稍后重试')
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
  await loadTasks()
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
