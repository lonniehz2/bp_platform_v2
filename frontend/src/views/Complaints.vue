<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">投诉管理</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="createVisible = true">新建投诉</el-button>

    </div>

    <el-alert type="info" :closable="false" show-icon :title="'投诉需在时限内办结，办结时填写处理意见'"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="complaintNo" label="投诉单号" width="170" />
      <el-table-column prop="complaintType" label="类型" width="130">
        <template #default="{ row }">{{ row.complaintTypeLabel || enumLabel('complaintType', row.complaintType) }}</template>
      </el-table-column>
      <el-table-column prop="handleStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.handleStatusLabel || enumLabel('complaintStatus', row.handleStatus) }}</template>
      </el-table-column>
      <el-table-column prop="submitterName" label="投诉人" width="120">
        <template #default="{ row }">{{ row.submitterName || row.personIdName || "-" }}</template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/complaints/{id}/close', '办结')">办结</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="createVisible" title="新建诉求" width="700px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="字段与后端 ComplaintCreateCmd 一致；带 * 为必填" />
      <el-form :model="form" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="诉求类型" required>
            <el-select v-model="form.complaintType" style="width:100%" data-testid="f-complaintType">
              <el-option label="投诉" value="COMPLAINT" />
              <el-option label="建议" value="SUGGEST" />
              <el-option label="咨询" value="CONSULT" />
              <el-option label="表扬" value="PRAISE" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="来源">
            <el-select v-model="form.source" style="width:100%" clearable data-testid="f-source">
              <el-option label="小程序" value="MINIAPP" />
              <el-option label="APP" value="APP" />
              <el-option label="电话" value="PHONE" />
              <el-option label="来访" value="WALKIN" />
              <el-option label="其他" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="标题" required>
            <el-input v-model="form.title" data-testid="f-title"
                      placeholder="一句话概括，≤255 字符" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="内容">
            <el-input v-model="form.content" type="textarea" :rows="3"
                      data-testid="f-content" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="关联人员 ID">
            <PersonPicker v-model="form.personId" width="240px" testid="person-picker" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="组织 ID">
            <el-input v-model="form.orgId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="提交人姓名">
            <el-input v-model="form.submitterName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="联系电话">
            <el-input v-model="form.submitterPhone" /></el-form-item></el-col>
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
/** 字段名严格对齐后端 ComplaintCreateCmd */
const form = reactive({
  complaintType: 'COMPLAINT',
  source: 'PHONE',
  title: '',
  content: '',
  personId: '',
  submitterName: '',
  submitterPhone: '',
  orgId: ''
})

async function load() {
  loading.value = true
  try {
    const d = await req.get('/complaints', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  // 必填项与后端 ComplaintCreateCmd 一致
  const missing = []
  if (!form.complaintType) missing.push('诉求类型')
  if (!form.title) missing.push('标题')
  if (missing.length) { ElMessage.warning('请填写：' + missing.join('、')); return }
  saving.value = true
  try {
    await req.post('/complaints', { ...form })
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
