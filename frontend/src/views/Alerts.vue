<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">告警处理</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button @click="loadStats">告警统计</el-button>
      <el-button type="success" @click="createVisible = true">新建告警</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon :title="'阈值告警由规则引擎产生；可转工单、升级或忽略'"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="alertType" label="告警类型" width="150">
        <template #default="{ row }">{{ row.alertTypeLabel || enumLabel('alertType', row.alertType) }}</template>
      </el-table-column>
      <el-table-column prop="alertLevel" label="级别" width="100">
        <template #default="{ row }">{{ row.alertLevelLabel || enumLabel('alertLevel', row.alertLevel) }}</template>
      </el-table-column>
      <el-table-column prop="alertStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.alertStatusLabel || enumLabel('alertStatus', row.alertStatus) }}</template>
      </el-table-column>
      <el-table-column prop="alertContent" label="内容" width="200" />
      <el-table-column label="操作" width="424" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/handle', '处理')">处理</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/resolve', '解决')">解决</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/ignore', '忽略')">忽略</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/escalate', '升级')">升级</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/to-workorder', '转工单')">转工单</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="createVisible" title="新建告警" width="700px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="字段与后端 AlertCreateCmd 一致；带 * 为必填" />
      <el-form :model="form" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="告警类别" required>
            <el-select v-model="form.alertCategory" style="width:100%" data-testid="f-alertCategory">
              <el-option label="安全隐患" value="SAFETY" />
              <el-option label="设备异常" value="DEVICE" />
              <el-option label="业务风险" value="BUSINESS" />
              <el-option label="违规行为" value="VIOLATION" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="告警级别" required>
            <el-select v-model="form.alertLevel" style="width:100%" data-testid="f-alertLevel">
              <el-option label="紧急" value="URGENT" />
              <el-option label="重要" value="IMPORTANT" />
              <el-option label="普通" value="NORMAL" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="告警类型" required>
            <el-input v-model="form.alertType" data-testid="f-alertType"
                      placeholder="如 ARREAR_RATE / DEVICE_OFFLINE" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="组织 ID">
            <el-input v-model="form.orgId" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="告警标题" required>
            <el-input v-model="form.alertTitle" data-testid="f-alertTitle"
                      placeholder="一句话说明问题，≤255 字符" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="告警内容">
            <el-input v-model="form.alertContent" type="textarea" :rows="3"
                      data-testid="f-alertContent" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="实际值">
            <el-input v-model="form.alertValue" placeholder="如 15%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="阈值">
            <el-input v-model="form.thresholdValue" placeholder="如 10%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="关联房源 ID">
            <el-input v-model="form.houseId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="关联人员 ID">
            <PersonPicker v-model="form.personId" width="240px" testid="person-picker" /></el-form-item></el-col>
        </el-row>
      </el-form>
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
import PersonPicker from '@/components/PersonPicker.vue'
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

/** 字段名严格对齐后端 AlertCreateCmd */
const form = reactive({
  alertCategory: 'SAFETY',
  alertType: '',
  alertLevel: 'NORMAL',
  alertTitle: '',
  alertContent: '',
  alertValue: '',
  thresholdValue: '',
  orgId: '',
  houseId: '',
  personId: ''
})

const SCHEMA = [
  { key: 'alertCategory', label: '告警类别', type: 'select', required: true, options: [
    { label: '安全隐患', value: 'SAFETY' }, { label: '设备异常', value: 'DEVICE' },
    { label: '业务风险', value: 'BUSINESS' }, { label: '违规行为', value: 'VIOLATION' }
  ] },
  { key: 'alertLevel', label: '告警级别', type: 'select', required: true, options: [
    { label: '紧急', value: 'URGENT' }, { label: '重要', value: 'IMPORTANT' },
    { label: '普通', value: 'NORMAL' }
  ] },
  { key: 'alertType', label: '告警类型', required: true, placeholder: '如 ARREAR_RATE / DEVICE_OFFLINE，≤40 字符' },
  { key: 'orgId', label: '组织 ID', placeholder: '可空，填真实主键' },
  { key: 'alertTitle', label: '告警标题', required: true, span: 24, placeholder: '一句话说明问题，≤255 字符' },
  { key: 'alertContent', label: '告警内容', type: 'textarea', span: 24, rows: 3 },
  { key: 'alertValue', label: '实际值', placeholder: '如 15%' },
  { key: 'thresholdValue', label: '阈值', placeholder: '如 10%' },
  { key: 'houseId', label: '关联房源 ID' },
  { key: 'personId', label: '关联人员 ID' }
]

async function load() {
  loading.value = true
  try {
    const d = await req.get('/alerts', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  // 必填项与 AlertCreateCmd 的 @NotBlank 一致
  const missing = []
  if (!form.alertCategory) missing.push('告警类别')
  if (!form.alertType) missing.push('告警类型')
  if (!form.alertLevel) missing.push('告警级别')
  if (!form.alertTitle) missing.push('告警标题')
  if (missing.length) { ElMessage.warning('请填写：' + missing.join('、')); return }

  saving.value = true
  try {
    await req.post('/alerts', { ...form })
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

async function actAction(row, path, label) {
  const { value } = await ElMessageBox.prompt('处理结果', label, { inputValue: '' })
  await req.post(pathTpl(path, row.id),
                 { handleUserId: 1, action: label, result: value })
  ElMessage.success(label + '成功'); load()
}
async function loadStats() {
  const r = await req.get('/alerts/stats')
  ElMessageBox.alert(JSON.stringify(r, null, 2).slice(0, 900), '告警统计')
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
