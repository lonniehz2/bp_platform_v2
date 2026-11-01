<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('exchange.title') }}</h3>
      <div class="spacer" />
      <OrgSelect v-model="orgId" width="200px" testid="ex-org" />
      <el-input v-model="keyword" :placeholder="t('exchange.keyword')" clearable style="width:180px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">{{ t('exchange.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('exchange.reset') }}</el-button>
      <el-button type="success" @click="createVisible = true">{{ t('exchange.create') }}</el-button>

    </div>

    <el-alert type="info" :closable="false" show-icon :title="'换房次数受限；「应换不换」按 1.5 倍租金计收'"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small" empty-text="暂无数据，可调整筛选条件或点击右上角新建">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="exchangeNo" :label="t('exchange.no')" width="170" />
      <el-table-column prop="personId" :label="t('exchange.person')" width="110">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="oldHouseId" :label="t('exchange.oldHouse')" width="120">
        <template #default="{ row }">{{ row.oldHouseIdName || row.oldHouseId }}</template>
      </el-table-column>
      <el-table-column prop="newHouseId" :label="t('exchange.newHouse')" width="120">
        <template #default="{ row }">{{ row.newHouseIdName || row.newHouseId }}</template>
      </el-table-column>
      <el-table-column prop="exchangeTimes" :label="t('exchange.times')" width="100" />
      <el-table-column prop="exchangeStatus" :label="t('exchange.status')" width="110">
        <template #default="{ row }">{{ row.exchangeStatusLabel || enumLabel('exchangeStatus', row.exchangeStatus) }}</template>
      </el-table-column>
      <el-table-column :label="t('exchange.actions')" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('exchange.detail') }}</el-button>
          <el-button link @click="actPlain(row, '/exchanges/{id}/submit', t('exchange.submit'))">{{ t('exchange.submit') }}</el-button>
          <el-dropdown trigger="click" style="margin-left:8px">
            <el-button link type="primary">{{ t('exchange.more') }}</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="actReason(row, '/exchanges/{id}/approve', '批准')">批准</el-dropdown-item>
                <el-dropdown-item @click="actReason(row, '/exchanges/{id}/reject', '驳回')">驳回</el-dropdown-item>
                <el-dropdown-item @click="actPlain(row, '/exchanges/{id}/complete', '完成')">完成</el-dropdown-item>
                <el-dropdown-item @click="actReason(row, '/exchanges/{id}/no-exchange', '登记')">应换不换</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <el-dialog v-model="createVisible" :title="t('exchange.createTitle')" width="720px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="字段与后端 ExchangeCreateCmd 一致；带 * 为必填" />
      <el-form :model="form" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('exchange.personId')" required>
            <PersonPicker v-model="form.personId" width="240px" testid="person-picker" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('exchange.type')" required>
            <el-select v-model="form.exchangeType" style="width:100%" data-testid="f-exchangeType">
              <el-option :label="t('exchange.voluntary')" value="VOLUNTARY" />
              <el-option :label="t('exchange.adjust')" value="ADJUST" />
              <el-option :label="t('exchange.expel')" value="EXPEL_RELOCATE" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('exchange.oldContract')" required>
            <el-input :model-value="auto.contractNo || form.oldContractId" disabled
                      data-testid="f-oldContractId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('exchange.oldHouseId')" required>
            <el-input :model-value="auto.houseName || form.oldHouseId" disabled
                      data-testid="f-oldHouseId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('exchange.newHouseId')" required>
            <el-input v-model="form.newHouseId" data-testid="f-newHouseId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('exchange.reasonCode')">
            <el-select v-model="form.exchangeReasonCode" style="width:100%" clearable>
              <el-option :label="t('exchange.marriage')" value="MARRIAGE" />
              <el-option :label="t('exchange.birth')" value="BIRTH" />
              <el-option :label="t('exchange.cohabit')" value="COHABIT" />
              <el-option :label="t('exchange.employment')" value="EMPLOYMENT" />
              <el-option :label="t('exchange.school')" value="SCHOOL" />
              <el-option :label="t('exchange.other')" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('exchange.oldFamily')">
            <el-input v-model="form.familySizeBefore" type="number" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('exchange.newFamily')">
            <el-input v-model="form.familySizeAfter" type="number" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item :label="t('exchange.reason')">
            <el-input v-model="form.exchangeReason" type="textarea" :rows="3"
                      data-testid="f-exchangeReason" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item :label="t('exchange.force')">
            <el-switch v-model="form.forceExchange" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('exchange.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('exchange.submitBtn') }}</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" :title="t('exchange.drawer')" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('exchange.detailTitle')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView，字段与中文名来自后端字段字典） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, watch, onMounted } from 'vue'
import PersonPicker from '@/components/PersonPicker.vue'
import OrgSelect from '@/components/OrgSelect.vue'
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

watch(() => form.personId, (pid) => fillFromPerson(pid))

const orgId = ref('')
const auto = reactive({ contractNo: '', houseName: '', orgName: '' })

/** 选择人员后自动带出原合同、原房源与原家庭人口 */
async function fillFromPerson(pid) {
  Object.assign(auto, { contractNo: '', houseName: '', orgName: '' })
  form.oldContractId = ''
  form.oldHouseId = ''
  if (!pid) return
  try {
    const ct = await req.get('/contracts/active-by-person/' + pid)
    if (ct && ct.contractStatus === 'EFFECTIVE') {
      form.oldContractId = ct.id
      form.oldHouseId = ct.houseId
      auto.contractNo = ct.contractNo
      auto.houseName = ct.houseIdName || ct.houseId
      auto.orgName = ct.orgIdName || ct.orgId
    } else if (ct) {
      ElMessage.warning('该人员合同当前为「' + (ct.contractStatusLabel || ct.contractStatus)
        + '」，仅履约中合同可发起换房')
    } else {
      ElMessage.warning('该人员没有生效中的合同，不能发起换房')
    }
    const gp = await req.get('/guarantee-profiles/person/' + pid).catch(() => null)
    if (gp && gp.familySize != null) form.familySizeBefore = gp.familySize
  } catch (e) { /* 保持手填 */ }
}

async function load() {
  loading.value = true
  try {
    const d = await req.get('/exchanges', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined,
                orgId: orgId.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  // 必填项与后端 ExchangeCreateCmd 一致
  const missing = []
  if (!form.personId) missing.push('换房人员')
  if (!form.exchangeType) missing.push('换房类型')
  if (!form.oldContractId) missing.push('原合同')
  if (!form.oldHouseId) missing.push('原房源')
  if (!form.newHouseId) missing.push('新房源')
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
