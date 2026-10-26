# -*- coding: utf-8 -*-
"""P2-2 报表导出任务：刷新、详情、补跑待执行。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'Reports.vue')
s = io.open(P, encoding='utf-8').read()

OLD_TOOLBAR = """      <h4 style="margin:0 0 12px">导出任务</h4>
      <el-table :data="tasks" border size="small">"""
NEW_TOOLBAR = """      <div class="toolbar" style="margin-bottom:12px">
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
      <el-table :data="filteredTasks" border size="small">"""
if OLD_TOOLBAR in s:
    s = s.replace(OLD_TOOLBAR, NEW_TOOLBAR, 1)

OLD_OPS = """          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览</el-button>
            <el-button link type="success" @click="download(row)">下载</el-button>
          </template>"""
NEW_OPS = """          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览</el-button>
            <el-button link type="success" @click="download(row)">下载</el-button>
            <el-button link @click="showTask(row)">任务详情</el-button>
          </template>"""
if OLD_OPS in s:
    s = s.replace(OLD_OPS, NEW_OPS, 1)
    s = s.replace('<el-table-column label="操作" width="170">',
                  '<el-table-column label="操作" width="230" fixed="right">', 1)

# 任务详情弹窗
if 'taskDetailVisible' not in s:
    s = s.replace("""    <el-dialog v-model="previewVisible\"""",
"""    <!-- 任务详情 -->
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

    <el-dialog v-model="previewVisible\"""", 1)

SCRIPT = """
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
    tasks.value = await rptApi.tasks() || []
  } catch (e) {
    ElMessage.error('导出任务加载失败')
  }
}

async function showTask(row) {
  try {
    taskDetail.value = await req.get(`/rpt/exports/${row.id}`) || row
  } catch (e) {
    taskDetail.value = row
  }
  taskDetailVisible.value = true
}

async function runPending() {
  runningPending.value = true
  try {
    const n = await req.post('/rpt/exports/run-pending')
    ElMessage.success(`已补跑 ${n} 个待执行任务`)
    loadTasks()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '补跑失败')
  } finally { runningPending.value = false }
}
"""

if 'loadTasks' not in s:
    s = s.replace('</script>', SCRIPT + '</script>', 1)

# 需要的 import
if 'computed' not in s.split('</script>')[0].split('<script setup>')[1][:400]:
    s = s.replace("import { ref, onMounted } from 'vue'",
                  "import { computed, ref, onMounted } from 'vue'", 1)
if "'@/api/request'" not in s:
    s = s.replace("import { rptApi } from '@/api/modules'",
                  "import { rptApi } from '@/api/modules'\nimport req from '@/api/request'", 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Reports.vue 已加任务筛选/详情/补跑')
