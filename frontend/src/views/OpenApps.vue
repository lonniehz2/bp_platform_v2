<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">开放平台</h3>
      <el-tag size="small" type="info">第三方/政务接入</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字/ID" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="openCreate">创建应用</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="'开放应用按 appKey 鉴权；密钥重置后旧密钥立即失效'" style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="appKey" label="AppKey" width="200" />
      <el-table-column prop="appName" label="应用名" width="150" />
      <el-table-column prop="appType" label="类型" width="120">
        <template #default="{ row }">{{ row.appTypeLabel || enumLabel('appType', row.appType) }}</template>
      </el-table-column>
      <el-table-column prop="appStatus" label="状态" width="100">
        <template #default="{ row }">{{ row.appStatusLabel || enumLabel('appStatus', row.appStatus) }}</template>
      </el-table-column>
      <el-table-column label="操作" :width="ROWACTIONS ? 300 : 250" fixed="right">
        <template #default="{ row }">
          <el-button link type="warning" @click="resetSecret(row)">重置密钥</el-button>
          <el-button link @click="openDetail(row)">详情</el-button>
          <el-button link :type="row.appStatus === 'ENABLED' ? 'warning' : 'success'"
                     @click="toggleAppStatus(row)">
            {{ row.appStatus === 'ENABLED' ? '停用' : '启用' }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

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
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { openApi } from '@/api/modules'
import req from '@/api/request'

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
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
