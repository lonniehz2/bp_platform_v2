<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">申诉管理</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="createVisible = true">新建申诉</el-button>
      <el-button @click="markTimeout">标记超时</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon :title="'申诉期限默认 10 个自然日；逾期未处理会标记超时'"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="appealNo" label="申诉单号" width="170" />
      <el-table-column prop="appealType" label="类型" width="130">
        <template #default="{ row }">{{ row.appealTypeLabel || enumLabel('appealType', row.appealType) }}</template>
      </el-table-column>
      <el-table-column prop="appealStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.appealStatusLabel || enumLabel('appealStatus', row.appealStatus) }}</template>
      </el-table-column>
      <el-table-column prop="personIdName" label="申请人" width="120">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/appeals/{id}/accept', '受理')">受理</el-button>
          <el-dropdown trigger="click" style="margin-left:8px">
            <el-button link type="primary">更多▾</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="actReason(row, '/api/v1/appeals/{id}/investigate', '调查')">调查</el-dropdown-item>
                <el-dropdown-item @click="actReason(row, '/api/v1/appeals/{id}/decide', '决定')">决定</el-dropdown-item>
                <el-dropdown-item @click="actPlain(row, '/api/v1/appeals/{id}/notify', '通知')">通知</el-dropdown-item>
                <el-dropdown-item @click="actReason(row, '/api/v1/appeals/{id}/withdraw', '撤回')">撤回</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="createVisible" title="新建申诉" width="700px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="字段与后端 AppealCreateCmd 一致；带 * 为必填" />
      <JsonForm :model="form" :schema="SCHEMA"
                @update:model="(m) => Object.assign(form, m)" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
/** 通用详情弹窗（复用 DetailView，字段与中文名来自后端字段字典） */
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import DetailView from '@/components/DetailView.vue'
import JsonForm from '@/components/JsonForm.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
const createVisible = ref(false)
/** 字段名严格对齐后端 AppealCreateCmd */
const form = reactive({
  bizType: 'APPLICATION',
  bizId: '',
  personId: '',
  orgId: '',
  appealType: 'OBJECTION',
  appealReason: '',
  appealEvidence: '',
  daysFromNow: 7
})

const SCHEMA = [
  { key: 'bizType', label: '业务类型', type: 'select', required: true, options: [
    { label: '申请', value: 'APPLICATION' }, { label: '审核', value: 'REVIEW' },
    { label: '年审', value: 'ANNUAL_REVIEW' }, { label: '公示', value: 'PUBLICITY' },
    { label: '退出', value: 'EXIT' }
  ] },
  { key: 'appealType', label: '申诉类型', type: 'select', required: true, options: [
    { label: '提交材料', value: 'SUBMIT' }, { label: '提出异议', value: 'OBJECTION' }
  ] },
  { key: 'bizId', label: '业务单据 ID', required: true, placeholder: '填真实主键' },
  { key: 'personId', label: '申诉人 ID', required: true },
  { key: 'orgId', label: '组织 ID' },
  { key: 'daysFromNow', label: '答复期限(天)', type: 'number', placeholder: '默认 7' },
  { key: 'appealReason', label: '申诉理由', type: 'textarea', required: true, span: 24, rows: 3 },
  { key: 'appealEvidence', label: '证据材料', type: 'textarea', span: 24, rows: 2,
    placeholder: '说明或链接，≤2000 字' }
]

async function load() {
  loading.value = true
  try {
    const d = await req.get('/appeals', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  // 必填项与 AppealCreateCmd 的校验注解一致
  const missing = []
  if (!form.bizType) missing.push('业务类型')
  if (!form.appealType) missing.push('申诉类型')
  if (!form.bizId) missing.push('业务单据 ID')
  if (!form.personId) missing.push('申诉人 ID')
  if (!form.appealReason) missing.push('申诉理由')
  if (missing.length) { ElMessage.warning('请填写：' + missing.join('、')); return }
  saving.value = true
  try {
    await req.post('/appeals', { ...form, daysFromNow: Number(form.daysFromNow) || 7 })
    ElMessage.success('创建成功')
    createVisible.value = false; load()
  } finally { saving.value = false }
}

/** 带原因的动作 */
async function actReason(row, path, label) {
  const { value } = await ElMessageBox.prompt('请输入' + label + '原因', label, {
    inputValue: ''
  })
  await req.post(`${pathTpl(path, row.id)}`, { reason: value })
  ElMessage.success(label + '成功'); load()
}
function pathTpl(p, id) { return p.replace('{id}', id) }

/** 无参数动作 */
async function actPlain(row, path, label) {
  await ElMessageBox.confirm('确认执行「' + label + '」？', label, { type: 'warning' })
  await req.post(pathTpl(path, row.id))
  ElMessage.success(label + '成功'); load()
}

async function markTimeout() {
  const r = await req.post('/appeals/mark-timeout')
  ElMessage.success('已标记超时：' + (r?.count ?? '完成')); load()
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
