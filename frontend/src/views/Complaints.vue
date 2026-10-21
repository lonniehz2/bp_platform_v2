<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">投诉管理</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>

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
      <el-table-column prop="complaintStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.complaintStatusLabel || enumLabel('complaintStatus', row.complaintStatus) }}</template>
      </el-table-column>
      <el-table-column prop="complainantPersonId" label="投诉人" width="120">
        <template #default="{ row }">{{ row.complainantPersonIdName || row.complainantPersonId }}</template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="actReason(row, '/api/v1/complaints/{id}/close', '办结')">办结</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="createVisible" title="新建" width="560px">
      <el-alert type="warning" :closable="false" show-icon
                title="字段取自后端 Cmd 定义，可直接编辑；数字 ID 请填真实主键" />
      <el-input v-model="json" type="textarea" :rows="16"
                style="margin-top:10px;font-family:monospace" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
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
const json = ref(JSON.stringify({"complainantPersonId": 1, "complaintType": "SERVICE", "complaintContent": "报修长时间未处理", "orgId": 1}, null, 2))

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
  let body
  try { body = JSON.parse(json.value) } catch (e) {
    ElMessage.error('JSON 格式错误'); return
  }
  saving.value = true
  try {
    await req.post('/complaints', body)
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
