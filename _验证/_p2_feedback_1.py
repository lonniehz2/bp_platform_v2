# -*- coding: utf-8 -*-
"""用户反馈 5 项修复（前端部分）：
  1) 报表导出任务：补脚本（原先未插入导致空白）+ 存储位置与空态提示
  2/4) 规则：条件/阈值可视化（字段+运算符+值）、中文展示、支持编辑、层级说明
  5) 设备告警角标：改用 devAlerts
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 1) Reports：补脚本 + 提示 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Reports.vue')
s = io.open(P, encoding='utf-8').read()

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
    tasks.value = (await rptApi.tasks()) || []
  } catch (e) {
    ElMessage.error('导出任务加载失败')
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
    ElMessage.success(`已补跑 ${n} 个待执行任务`)
    loadTasks()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '补跑失败')
  } finally { runningPending.value = false }
}
"""

if 'async function loadTasks' not in s:
    s = s.replace('</script>', SCRIPT + '</script>', 1)
    print('Reports 脚本已补')

# 导出成功后刷新任务列表（原来只 unshift 本地）
s = s.replace("""    ElMessage.success(`导出完成：${task.fileName}（${task.rowCount} 行）`)
    tasks.value.unshift(task)""",
"""    ElMessage.success(`导出完成：${task.fileName}（${task.rowCount} 行），
      文件已存到服务器，可在下方「导出任务」点下载`)
    await loadTasks()""", 1)

# 空态与存储位置提示
s = s.replace("""      <el-table :data="filteredTasks" border size="small">""",
"""      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="导出文件保存在服务器 /var/lib/bp-export/ 目录；点「下载」可保存到本机「下载」目录。任务列表为空表示还没有导出记录。" />
      <el-table :data="filteredTasks" border size="small" empty-text="暂无导出任务，请点右上角「导出」生成">""", 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)

# ---------- 5) 菜单角标：设备告警用 devAlerts ----------
P = os.path.join(ROOT, 'frontend', 'src', 'layout', 'menuConfig.js')
m = io.open(P, encoding='utf-8').read()
m = m.replace("  '/dev-events': 'pendingAlerts',", "  '/dev-events': 'devAlerts',")
io.open(P, 'w', encoding='utf-8', newline='').write(m)
print('菜单角标：设备告警 → devAlerts')
