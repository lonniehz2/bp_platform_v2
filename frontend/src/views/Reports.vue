<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="reportCode" :placeholder="t('report.select')" style="width:220px"
                   @change="onQuery">
          <el-option v-for="r in reports" :key="r.reportCode"
                     :label="reportLabel(r)" :value="r.reportCode" />
        </el-select>
        <el-button type="primary" @click="onQuery">{{ t('report.search') }}</el-button>
        <el-button @click="resetQuery">{{ t('report.reset') }}</el-button>
        <div class="spacer" />
        <el-select v-model="exportFormat" style="width:120px" data-testid="export-format">
          <el-option label="CSV" value="CSV" />
          <el-option label="Excel" value="EXCEL" />
        </el-select>
        <el-button type="success" :loading="exporting" @click="onExport">
          <el-icon><Download /></el-icon>{{ t('report.export') }}
        </el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column v-for="c in columns" :key="c.key"
                         :prop="c.key" :label="colLabel(c.title)" show-overflow-tooltip />
        <el-table-column v-if="!columns.length" :label="t('report.hint')">
          <template #default>{{ t('report.selectReport') }}</template>
        </el-table-column>
      </el-table>

      <div class="muted" style="margin-top:10px">{{ summary }}</div>

      <el-pagination
        v-model:current-page="pageNum"
        v-model:page-size="pageSize"
        :total="+total || 0"
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
        <h4 style="margin:0">{{ t('report.exportTasks') }}</h4>
        <div class="spacer" />
        <el-select v-model="taskStatusFilter" :placeholder="t('report.taskStatus')" clearable
                   style="width:120px" @change="applyTaskFilter">
          <el-option :label="t('report.pending')" value="PENDING" />
          <el-option :label="t('report.running')" value="RUNNING" />
          <el-option :label="t('report.success')" value="SUCCESS" />
          <el-option :label="t('report.failed')" value="FAILED" />
        </el-select>
        <el-button @click="loadTasks">{{ t('report.refresh') }}</el-button>
        <el-button type="warning" :loading="runningPending" @click="runPending">{{ t('report.runPending') }}
        </el-button>
      </div>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                :title="t('report.taskTip')" />
      <el-table :data="filteredTasks" border size="small" :empty-text="t('report.noTasks')">
        <el-table-column prop="taskNo" :label="t('report.taskNo')" width="160" />
        <el-table-column prop="fileName" :label="t('report.fileName')" min-width="200" />
        <el-table-column prop="rowCount" :label="t('report.rowCount')" width="80" />
        <el-table-column prop="taskStatus" :label="t('report.status')" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.taskStatus === 'SUCCESS' ? 'success' : 'info'">
              {{ row.taskStatusLabel || enumLabel('taskStatus', row.taskStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="fileUrl" :label="t('report.fileUrl')" min-width="240"
                         show-overflow-tooltip />
        <el-table-column :label="t('report.actions')" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">{{ t('report.preview') }}</el-button>
            <el-button link type="success" @click="download(row)">{{ t('report.download') }}</el-button>
            <el-button link @click="showTask(row)">{{ t('report.taskDetail') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 任务详情 -->
    <el-dialog v-model="taskDetailVisible" :title="t('report.detailTitle')" width="620px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item :label="t('report.taskNo')">{{ taskDetail.taskNo }}</el-descriptions-item>
        <el-descriptions-item :label="t('report.report')">{{ taskDetail.reportCode }}</el-descriptions-item>
        <el-descriptions-item :label="t('report.fileName')">{{ taskDetail.fileName }}</el-descriptions-item>
        <el-descriptions-item :label="t('report.status')">
          {{ taskDetail.taskStatusLabel || enumLabel('taskStatus', taskDetail.taskStatus) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('report.rowCount')">{{ taskDetail.rowCount }}</el-descriptions-item>
        <el-descriptions-item :label="t('report.cost')">{{ taskDetail.costMs }} ms</el-descriptions-item>
        <el-descriptions-item :label="t('report.serverPath')">
          {{ taskDetail.fileUrl || '—' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('report.created')">
          {{ taskDetail.createTime || '—' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('report.failReason')">
          {{ taskDetail.errorMsg || '—' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="taskDetailVisible = false">{{ t('report.close') }}</el-button>
        <el-button type="success" @click="download(taskDetail)">{{ t('report.download') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="previewVisible"
               :title="t('report.previewTitle', { n: previewText.length.toLocaleString(getLocale()) })"
               width="820px">
      <pre class="csv-preview">{{ previewText }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { computed, ref, onMounted } from 'vue'
import { enumLabel } from '@/constants/enums'
import { ElMessage } from 'element-plus'
import { rptApi } from '@/api/modules'
import req from '@/api/request'

const { t, locale } = useI18n()

const REPORT_EN = {
  HOUSE_LEDGER: 'Housing Ledger',
  CONTRACT_LEDGER: 'Contract Ledger',
  ARREARS_LEDGER: 'Arrears Ledger'
}
const COL_EN = {
  '房源编号': 'Housing Code', '房源名称': 'Housing Name', '房源类型': 'Housing Type',
  '面积(㎡)': 'Area (m²)', '房源状态': 'Housing Status',
  '合同号': 'Contract No.', '承租人': 'Lessee', '起租日': 'Lease Start',
  '止租日': 'Lease End', '月租金': 'Monthly Rent', '状态': 'Status',
  '账单号': 'Bill No.', '缴费人': 'Payer', '账期': 'Billing Period',
  '应付金额': 'Payable', '缴费截止日': 'Due Date'
}
function isEn() {
  return locale.value === 'en-US'
}
function reportLabel(r) {
  return isEn() ? (REPORT_EN[r.reportCode] || r.reportName) : r.reportName
}
function colLabel(title) {
  return isEn() ? (COL_EN[title] || title) : title
}
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
    ElMessage.success(t('report.exportDone', { name: task.fileName, rows: task.rowCount }))
    await loadTasks()
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
    ElMessage.error(t('report.downloadFailed'))
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

// ---------------- 导出任务：筛选 / 详情 / 补跑 ----------------
const taskStatusFilter = ref('')
const taskDetailVisible = ref(false)
const taskDetail = ref({})
const runningPending = ref(false)

const filteredTasks = computed(() => taskStatusFilter.value
  ? tasks.value.filter((t) => t.taskStatus === taskStatusFilter.value)
  : tasks.value)

function applyTaskFilter() { /* filteredTasks 由 computed 派生 */ }

async function loadTasks() {
  try {
    tasks.value = (await rptApi.tasks()) || []
  } catch (e) {
    ElMessage.error(t('report.taskLoadFailed'))
  }
}

async function showTask(row) {
  try {
    taskDetail.value = (await rptApi.task(row.id)) || row
  } catch (e) {
    taskDetail.value = row
  }
  taskDetailVisible.value = true
}

async function runPending() {
  runningPending.value = true
  try {
    const n = await rptApi.runPending()
    ElMessage.success(t('report.runDone', { n }))
    loadTasks()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('report.recoverFailed'))
  } finally { runningPending.value = false }
}
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
