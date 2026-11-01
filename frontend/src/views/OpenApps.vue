<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('open.title') }}</h3>
      <el-tag size="small" type="info">第三方/政务接入</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" :placeholder="t('open.keyword')" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">{{ t('open.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('open.reset') }}</el-button>
      <el-button type="success" @click="openCreate">{{ t('open.create') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="'开放应用按 appKey 鉴权；密钥重置后旧密钥立即失效'" style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="appKey" :label="t('open.appKey')" width="200" />
      <el-table-column prop="appName" :label="t('open.appName')" width="150" />
      <el-table-column prop="appType" :label="t('open.type')" width="120">
        <template #default="{ row }">{{ row.appTypeLabel || enumLabel('appType', row.appType) }}</template>
      </el-table-column>
      <el-table-column prop="appStatus" :label="t('open.status')" width="100">
        <template #default="{ row }">{{ row.appStatusLabel || enumLabel('appStatus', row.appStatus) }}</template>
      </el-table-column>
      <el-table-column :label="t('open.actions')" :width="ROWACTIONS ? 300 : 250" fixed="right">
        <template #default="{ row }">
          <el-button link type="warning" @click="resetSecret(row)">{{ t('open.resetSecret') }}</el-button>
          <el-button link @click="openDetail(row)">{{ t('open.detail') }}</el-button>
          <el-button link :type="row.appStatus === 'ENABLED' ? 'warning' : 'success'"
                     @click="toggleAppStatus(row)">
            {{ row.appStatus === 'ENABLED' ? t('open.disable') : t('open.enable') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <!-- 写操作表单（字段按后端 Cmd 定义配置） -->
    <el-dialog v-model="formVisible" :title="formTitle" width="560px">
      <el-form :model="model" label-width="120px">
        <el-form-item v-for="f in fields" :key="f.key" :label="f.label">
          <el-input v-if="f.type === 'text'" v-model="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'textarea'" type="textarea" :rows="3"
                    v-model="model[f.key]" :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'number'" v-model.number="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-date-picker v-else-if="f.type === 'date'" v-model="model[f.key]"
                          type="date" value-format="YYYY-MM-DD" style="width:100%" />
          <el-select v-else-if="f.type === 'select'" v-model="model[f.key]"
                     style="width:100%">
            <el-option v-for="o in f.options" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>
          <el-switch v-else-if="f.type === 'bool'" v-model="model[f.key]" />
        </el-form-item>
      </el-form>
      <el-alert v-if="formNote" :closable="false" show-icon type="warning"
                :title="formNote" style="margin-top:8px" />
      <template #footer>
        <el-button @click="formVisible = false">{{ t('open.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="submit">{{ t('open.submit') }}</el-button>
      </template>
    </el-dialog>


    <!-- ==================== Webhook 订阅 ==================== -->
    <div class="page-card">
      <div class="toolbar">
        <h4 style="margin:0">{{ t('open.hookTitle') }}</h4>
        <el-tag size="small" type="info">{{ t('open.hookHint') }}</el-tag>
        <div class="spacer" />
        <el-button type="success" @click="openHook">{{ t('open.newHook') }}</el-button>
        <el-button @click="loadHooks">{{ t('open.refresh') }}</el-button>
      </div>

      <el-table :data="hooks" v-loading="hookLoading" border size="small">
        <el-table-column prop="hookName" :label="t('open.hookName')" width="160" />
        <el-table-column prop="callbackUrl" :label="t('open.callback')" min-width="260"
                         show-overflow-tooltip />
        <el-table-column prop="eventTypes" :label="t('open.events')" min-width="180"
                         show-overflow-tooltip />
        <el-table-column prop="retryTimes" :label="t('open.retries')" width="100" />
        <el-table-column prop="timeoutMs" :label="t('open.timeout')" width="100" />
        <el-table-column prop="hookStatus" :label="t('open.status')" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.hookStatus === 'ENABLED' ? 'success' : 'info'">
              {{ row.hookStatus === 'ENABLED' ? t('open.enabled') : t('open.disabled') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link :type="row.hookStatus === 'ENABLED' ? 'warning' : 'success'"
                       @click="toggleHook(row)">
              {{ row.hookStatus === 'ENABLED' ? t('open.disable') : t('open.enable') }}
            </el-button>
            <el-button link type="primary" @click="publishTest(row)">{{ t('open.test') }}</el-button>
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
        <el-select v-model="logStatus" :placeholder="t('open.logStatus')" clearable style="width:130px"
                   @change="loadLogs">
          <el-option :label="t('open.pending')" value="PENDING" />
          <el-option :label="t('open.success')" value="SUCCESS" />
          <el-option :label="t('open.failed')" value="FAILED" />
        </el-select>
        <el-button type="primary" @click="loadLogs">{{ t('open.search') }}</el-button>
        <el-button type="warning" :loading="retrying" @click="retryFailed">{{ t('open.retryFailed') }}</el-button>
      </div>

      <el-table :data="logs" v-loading="logLoading" border size="small">
        <el-table-column prop="eventType" :label="t('open.eventType')" width="170" />
        <el-table-column prop="eventId" :label="t('open.eventId')" width="170" />
        <el-table-column prop="pushStatus" :label="t('open.status')" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.pushStatus === 'SUCCESS' ? 'success'
              : (row.pushStatus === 'FAILED' ? 'danger' : 'warning')">
              {{ logStatusLabel(row.pushStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="httpStatus" label="HTTP" width="80" />
        <el-table-column prop="retryCount" :label="t('open.retry')" width="80" />
        <el-table-column prop="pushTime" :label="t('open.pushTime')" width="170" />
        <el-table-column prop="responseBody" :label="t('open.response')" min-width="220"
                         show-overflow-tooltip />
        <el-table-column prop="payload" :label="t('open.payload')" min-width="200" show-overflow-tooltip />
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="+logTotal || 0" :page-size="logQuery.pageSize"
                     :current-page="logQuery.pageNum"
                     @current-change="(p) => { logQuery.pageNum = p; loadLogs() }" />
    </div>

    <!-- 新建 Webhook -->
    <el-dialog v-model="hookVisible" :title="t('open.newHookTitle')" width="560px">
      <el-form :model="hf" label-width="110px">
        <el-form-item :label="t('open.hookName')" required>
          <el-input v-model="hf.hookName" :placeholder="t('open.hookNameHint')" />
        </el-form-item>
        <el-form-item :label="t('open.callback')" required>
          <el-input v-model="hf.callbackUrl" :placeholder="t('open.callbackHint')" />
        </el-form-item>
        <el-form-item :label="t('open.events')" required>
          <el-input v-model="hf.eventTypes"
                    :placeholder="t('open.eventHint')" />
        </el-form-item>
        <el-form-item :label="t('open.retries')">
          <el-input-number v-model="hf.retryTimes" :min="0" :max="10" style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('open.timeout')">
          <el-input-number v-model="hf.timeoutMs" :min="1000" :step="1000"
                           style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="hookVisible = false">{{ t('open.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateHook">{{ t('open.save') }}</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" :title="t('open.drawer')" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { openApi } from '@/api/modules'
import req from '@/api/request'

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const detailVisible = ref(false)
const detail = ref(null)

const formVisible = ref(false)
const formTitle = ref('')
const formNote = ref('')
const fields = [
  { key: 'appName', label: '应用名称', type: 'text' },
  { key: 'appType', label: '应用类型', type: 'select', options: [{ value: 'THIRD_PARTY', label: '第三方' }, { value: 'INTERNAL', label: '内部' }, { value: 'GOV', label: '政务' }] },
  { key: 'ownerOrg', label: '所属单位', type: 'text' },
  { key: 'contactName', label: '联系人', type: 'text' },
  { key: 'contactPhone', label: '联系电话', type: 'text' },
  { key: 'ipWhitelist', label: 'IP白名单', type: 'text' },
  { key: 'qpsLimit', label: 'QPS限流', type: 'number' },
  { key: 'dailyQuota', label: '日调用配额', type: 'number' },
  { key: 'scopeCodes', label: '授权接口范围', type: 'text' },
  { key: 'expireDate', label: '有效期', type: 'date' }
]
const model = reactive({})

// 必填字段（取自后端 Cmd 的 @NotNull）
const REQUIRED = ['appName', 'appType']
let submitFn = null


async function load() {
  loading.value = true
  try {
    const data = await openApi.apps({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = data.rows || data || []
    total.value = Number(data.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}

function reload() { pageNum.value = 1; load() }

/** 应用启用 / 停用 */
async function toggleAppStatus(row) {
  const next = row.appStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.post(`/open/apps/${row.id}/status`, { status: next })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

function openDetail(row) { detail.value = row; detailVisible.value = true }

function openForm(title, fieldDefs, fn, preset = {}, note = '') {
  formTitle.value = title
  formNote.value = note
  Object.keys(model).forEach((k) => delete model[k])
  fieldDefs.forEach((f) => { model[f.key] = preset[f.key] ?? f.default ?? '' })
  submitFn = fn
  formVisible.value = true
}

/** 必填校验（字段级，依赖后端 Cmd 的 @NotNull 语义）。 */
function validateForm() {
  const missing = fields.filter((f) => REQUIRED.includes(f.key)
    && (model[f.key] === '' || model[f.key] === null || model[f.key] === undefined))
  if (missing.length) {
    ElMessage.warning('请填写：' + missing.map((f) => f.label).join('、'))
    return false
  }
  // 数字类基本合法性
  for (const f of fields) {
    if (f.type === 'number' && model[f.key] !== '' && model[f.key] !== null
        && Number.isNaN(Number(model[f.key]))) {
      ElMessage.warning(f.label + '必须是数字')
      return false
    }
  }
  return true
}

async function submit() {
  if (!validateForm()) return
  saving.value = true
  try {
    await submitFn({ ...model })
    ElMessage.success('操作成功')
    formVisible.value = false
    load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}

function openCreate() {
  openForm('创建开放应用', fields, (m) => openApi.createApp(m),
    { appType: 'THIRD_PARTY', qpsLimit: 20, scopeCodes: '*' },
    '创建成功后 AppSecret 只显示这一次，请立即保存')
}
async function resetSecret(row) {
  await ElMessageBox.confirm('重置后旧密钥立即失效，确认继续？', '提示',
    { type: 'warning' })
  const r = await openApi.resetSecret(row.id)
  ElMessageBox.alert(`新密钥（仅此一次）：\n${r.appSecret}`, '请立即保存',
    { type: 'success' })
}

function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}

onMounted(load)
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
  if (!/^https?:\/\//i.test(hf.callbackUrl)) {
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
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
