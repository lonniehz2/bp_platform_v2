# -*- coding: utf-8 -*-
"""P2-1 开放平台：Webhook 订阅 + 投递日志。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'OpenApps.vue')
s = io.open(P, encoding='utf-8').read()

TPL = """
    <!-- ==================== Webhook 订阅 ==================== -->
    <div class="page-card">
      <div class="toolbar">
        <h4 style="margin:0">Webhook 订阅</h4>
        <el-tag size="small" type="info">业务事件推送到第三方回调地址</el-tag>
        <div class="spacer" />
        <el-button type="success" @click="openHook">新建订阅</el-button>
        <el-button @click="loadHooks">刷新</el-button>
      </div>

      <el-table :data="hooks" v-loading="hookLoading" border size="small">
        <el-table-column prop="hookName" label="名称" width="160" />
        <el-table-column prop="callbackUrl" label="回调地址" min-width="260"
                         show-overflow-tooltip />
        <el-table-column prop="eventTypes" label="订阅事件" min-width="180"
                         show-overflow-tooltip />
        <el-table-column prop="retryTimes" label="重试次数" width="100" />
        <el-table-column prop="timeoutMs" label="超时(ms)" width="100" />
        <el-table-column prop="hookStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.hookStatus === 'ENABLED' ? 'success' : 'info'">
              {{ row.hookStatus === 'ENABLED' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link :type="row.hookStatus === 'ENABLED' ? 'warning' : 'success'"
                       @click="toggleHook(row)">
              {{ row.hookStatus === 'ENABLED' ? '停用' : '启用' }}
            </el-button>
            <el-button link type="primary" @click="publishTest(row)">发布测试</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!hooks.length" class="muted" style="margin-top:8px">
        暂无订阅；新建后业务事件会按「订阅事件」推送到回调地址
      </div>
    </div>

    <!-- ==================== 投递日志 ==================== -->
    <div class="page-card">
      <div class="toolbar">
        <h4 style="margin:0">投递日志</h4>
        <div class="spacer" />
        <el-select v-model="logStatus" placeholder="投递状态" clearable style="width:130px"
                   @change="loadLogs">
          <el-option label="待推送" value="PENDING" />
          <el-option label="成功" value="SUCCESS" />
          <el-option label="失败" value="FAILED" />
        </el-select>
        <el-button type="primary" @click="loadLogs">查询</el-button>
        <el-button type="warning" :loading="retrying" @click="retryFailed">重试失败</el-button>
      </div>

      <el-table :data="logs" v-loading="logLoading" border size="small">
        <el-table-column prop="eventType" label="事件类型" width="170" />
        <el-table-column prop="eventId" label="事件ID" width="170" />
        <el-table-column prop="pushStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.pushStatus === 'SUCCESS' ? 'success'
              : (row.pushStatus === 'FAILED' ? 'danger' : 'warning')">
              {{ logStatusLabel(row.pushStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="httpStatus" label="HTTP" width="80" />
        <el-table-column prop="retryCount" label="重试" width="80" />
        <el-table-column prop="pushTime" label="推送时间" width="170" />
        <el-table-column prop="responseBody" label="响应" min-width="220"
                         show-overflow-tooltip />
        <el-table-column prop="payload" label="报文" min-width="200" show-overflow-tooltip />
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="logTotal" :page-size="logQuery.pageSize"
                     :current-page="logQuery.pageNum"
                     @current-change="(p) => { logQuery.pageNum = p; loadLogs() }" />
    </div>

    <!-- 新建 Webhook -->
    <el-dialog v-model="hookVisible" title="新建 Webhook 订阅" width="560px">
      <el-form :model="hf" label-width="110px">
        <el-form-item label="名称" required>
          <el-input v-model="hf.hookName" placeholder="如：住房局报送推送" />
        </el-form-item>
        <el-form-item label="回调地址" required>
          <el-input v-model="hf.callbackUrl" placeholder="https://example.com/webhook" />
        </el-form-item>
        <el-form-item label="订阅事件" required>
          <el-input v-model="hf.eventTypes"
                    placeholder="逗号分隔，如 CONTRACT_SIGNED,BILL_OVERDUE；* 表示全部" />
        </el-form-item>
        <el-form-item label="重试次数">
          <el-input-number v-model="hf.retryTimes" :min="0" :max="10" style="width:100%" />
        </el-form-item>
        <el-form-item label="超时(ms)">
          <el-input-number v-model="hf.timeoutMs" :min="1000" :step="1000"
                           style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="hookVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateHook">保存</el-button>
      </template>
    </el-dialog>
"""

if 'Webhook 订阅' not in s:
    s = s.replace("""    <el-drawer v-model="detailVisible" title="明细（原始数据）" size="520px">""",
                  TPL + """
    <el-drawer v-model="detailVisible" title="明细（原始数据）" size="520px">""", 1)

SCRIPT = """
// ---------------- Webhook 订阅 ----------------
const hooks = ref([])
const hookLoading = ref(false)
const hookVisible = ref(false)
const hf = reactive({ hookName: '', callbackUrl: '', eventTypes: '',
  retryTimes: 3, timeoutMs: 5000 })

async function loadHooks() {
  hookLoading.value = true
  try {
    hooks.value = await req.get('/open/webhooks') || []
  } catch (e) {
    hooks.value = []
  } finally { hookLoading.value = false }
}

function openHook() {
  Object.assign(hf, { hookName: '', callbackUrl: '', eventTypes: '',
    retryTimes: 3, timeoutMs: 5000 })
  hookVisible.value = true
}

async function doCreateHook() {
  if (!hf.hookName || !hf.callbackUrl || !hf.eventTypes) {
    ElMessage.warning('名称、回调地址、订阅事件为必填'); return
  }
  if (!/^https?:\\/\\//i.test(hf.callbackUrl)) {
    ElMessage.warning('回调地址需以 http:// 或 https:// 开头'); return
  }
  saving.value = true
  try {
    await req.post('/open/webhooks', { ...hf })
    ElMessage.success('订阅已创建')
    hookVisible.value = false
    loadHooks()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally { saving.value = false }
}

async function toggleHook(row) {
  const next = row.hookStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  await ElMessageBox.confirm(
    `确认${next === 'ENABLED' ? '启用' : '停用'}订阅「${row.hookName}」？`,
    next === 'ENABLED' ? '启用' : '停用', { type: 'warning' })
  await req.post(`/open/webhooks/${row.id}/status`, { status: next })
  ElMessage.success('已更新')
  loadHooks()
}

/** 发布一条测试事件，验证回调是否可达 */
async function publishTest(row) {
  const { value } = await ElMessageBox.prompt(
    '事件类型（需在该订阅的事件列表内）', '发布测试事件',
    { inputValue: (row.eventTypes || '').split(',')[0] || 'TEST',
      inputValidator: (v) => (v && v.trim() ? true : '请填写事件类型') })
  const payloadStr = '{"test":true,"source":"platform"}'
  const n = await req.post('/open/webhooks/publish', {
    eventType: value.trim(), payload: JSON.parse(payloadStr)
  })
  ElMessage.success(`已推送 ${n} 个订阅，可在下方投递日志查看结果`)
  loadLogs()
}

// ---------------- 投递日志 ----------------
const logs = ref([])
const logTotal = ref(0)
const logLoading = ref(false)
const logStatus = ref('')
const retrying = ref(false)
const logQuery = reactive({ pageNum: 1, pageSize: 20 })

function logStatusLabel(s) {
  return { PENDING: '待推送', SUCCESS: '成功', FAILED: '失败' }[s] || s
}

async function loadLogs() {
  logLoading.value = true
  try {
    const d = await req.get('/open/webhook-logs', {
      params: { pageNum: logQuery.pageNum, pageSize: logQuery.pageSize,
        pushStatus: logStatus.value || undefined }
    })
    logs.value = d.rows || []
    logTotal.value = Number(d.total || 0)
  } catch (e) {
    logs.value = []; logTotal.value = 0
  } finally { logLoading.value = false }
}

async function retryFailed() {
  retrying.value = true
  try {
    const n = await req.post('/open/webhook-logs/retry?limit=20')
    ElMessage.success(`已重试 ${n} 条失败推送`)
    loadLogs()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '重试失败')
  } finally { retrying.value = false }
}

onMounted(() => { loadHooks(); loadLogs() })
"""

if 'loadHooks' not in s:
    s = s.replace('</script>', SCRIPT + '</script>', 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('OpenApps.vue 已加 Webhook 与投递日志')
