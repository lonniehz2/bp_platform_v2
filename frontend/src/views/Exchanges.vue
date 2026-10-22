<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">换房管理</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="createVisible = true">新建换房</el-button>

    </div>

    <el-alert type="info" :closable="false" show-icon :title="'换房次数受限；「应换不换」按 1.5 倍租金计收'"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="exchangeNo" label="换房单号" width="170" />
      <el-table-column prop="personId" label="人员" width="110">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="oldHouseId" label="原房源" width="120">
        <template #default="{ row }">{{ row.oldHouseIdName || row.oldHouseId }}</template>
      </el-table-column>
      <el-table-column prop="newHouseId" label="新入住" width="120">
        <template #default="{ row }">{{ row.newHouseIdName || row.newHouseId }}</template>
      </el-table-column>
      <el-table-column prop="exchangeStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.exchangeStatusLabel || enumLabel('exchangeStatus', row.exchangeStatus) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="270" fixed="right">
        <template #default="{ row }">
          <el-button link @click="actPlain(row, '/api/v1/exchanges/{id}/submit', '提交')">提交</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/exchanges/{id}/approve', '批准')">批准</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/exchanges/{id}/reject', '驳回')">驳回</el-button>
          <el-button link @click="actPlain(row, '/api/v1/exchanges/{id}/complete', '完成')">完成</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/exchanges/{id}/no-exchange', '登记')">应换不换</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="createVisible" title="新建换房申请" width="720px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="字段与后端 ExchangeCreateCmd 一致；带 * 为必填" />
      <el-form :model="form" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="人员 ID" required>
            <PersonPicker v-model="form.personId" width="240px" testid="person-picker" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="换房类型" required>
            <el-select v-model="form.exchangeType" style="width:100%" data-testid="f-exchangeType">
              <el-option label="自愿换房" value="VOLUNTARY" />
              <el-option label="统筹调整" value="ADJUST" />
              <el-option label="清退安置" value="EXPEL_RELOCATE" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="原合同 ID" required>
            <el-input v-model="form.oldContractId" data-testid="f-oldContractId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="原房源 ID" required>
            <el-input v-model="form.oldHouseId" data-testid="f-oldHouseId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="新房源 ID" required>
            <el-input v-model="form.newHouseId" data-testid="f-newHouseId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="换房原因码">
            <el-select v-model="form.exchangeReasonCode" style="width:100%" clearable>
              <el-option label="结婚" value="MARRIAGE" />
              <el-option label="生育" value="BIRTH" />
              <el-option label="同住" value="COHABIT" />
              <el-option label="就业" value="EMPLOYMENT" />
              <el-option label="就学" value="SCHOOL" />
              <el-option label="其他" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="原家庭人口">
            <el-input v-model="form.familySizeBefore" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="现家庭人口">
            <el-input v-model="form.familySizeAfter" type="number" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="换房原因">
            <el-input v-model="form.exchangeReason" type="textarea" :rows="3"
                      data-testid="f-exchangeReason" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="强制换房">
            <el-switch v-model="form.forceExchange" /></el-form-item></el-col>
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
</template>

<script setup>
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
/** 字段名严格对齐后端 ExchangeCreateCmd */
const form = reactive({
  personId: '',
  exchangeType: 'VOLUNTARY',
  oldContractId: '',
  oldHouseId: '',
  newHouseId: '',
  exchangeReasonCode: '',
  exchangeReason: '',
  familySizeBefore: null,
  familySizeAfter: null,
  forceExchange: false
})

async function load() {
  loading.value = true
  try {
    const d = await req.get('/exchanges', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  // 必填项与后端 ExchangeCreateCmd 一致
  const missing = []
  if (!form.personId) missing.push('人员 ID')
  if (!form.exchangeType) missing.push('换房类型')
  if (!form.oldContractId) missing.push('原合同 ID')
  if (!form.oldHouseId) missing.push('原房源 ID')
  if (!form.newHouseId) missing.push('新房源 ID')
  if (missing.length) { ElMessage.warning('请填写：' + missing.join('、')); return }
  saving.value = true
  try {
    await req.post('/exchanges', { ...form })
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

// 待办中心「待审换房」跳转过来时带 pending=1
if (/pending=1/.test(window.location.hash) && typeof xf !== 'undefined') {
  xf.status = 'APPLYING'
}
onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
