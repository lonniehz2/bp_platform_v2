<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('credit.title') }}</h3>
      <div class="spacer" />
      <el-input v-model="keyword" :placeholder="t('credit.keyword')" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">{{ t('credit.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('credit.reset') }}</el-button>
      <el-button type="success" @click="createVisible = true">{{ t('credit.create') }}</el-button>
      <el-button @click="scanExpired">{{ t('credit.scan') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon :title="t('miscPage.creditsTip')"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('misc.emptyDefault')">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="personId" :label="t('credit.person')" width="120">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="violationType" :label="t('credit.type')" width="140">
        <template #default="{ row }">{{ row.violationTypeLabel || enumLabel('creditType', row.violationType) }}</template>
      </el-table-column>
      <el-table-column prop="sanctionType" :label="t('credit.level')" width="100">
        <template #default="{ row }">{{ row.sanctionTypeLabel || enumLabel('creditLevel', row.sanctionType) }}</template>
      </el-table-column>
      <el-table-column prop="status" :label="t('credit.status')" width="110">
        <template #default="{ row }">{{ row.statusLabel || enumLabel('creditStatus', row.status) }}</template>
      </el-table-column>
      <el-table-column prop="banEndDate" :label="t('credit.banEnd')" width="110" />
      <el-table-column :label="t('credit.actions')" width="250" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('credit.detail') }}</el-button>
          <el-button link type="primary" @click="actReason(row, '/credits/{id}/revoke', t('credit.revoke'))">{{ t('credit.revoke') }}</el-button>
          <el-button link type="primary" @click="actReason(row, '/credits/{id}/expire', t('credit.expire'))">{{ t('credit.expire') }}</el-button>
          <el-button link @click="actPlain(row, '/credits/{id}/push', t('credit.push'))">{{ t('credit.push') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <el-dialog v-model="createVisible" :title="t('credit.createTitle')" width="720px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="字段与后端 CreditCreateCmd 一致；带 * 为必填" />
      <el-form :model="form" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('credit.personId')" required>
            <PersonPicker v-model="form.personId" width="240px" testid="person-picker" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('credit.violationType')" required>
            <el-select v-model="form.violationType" style="width:100%" data-testid="f-violationType">
              <el-option :label="t('credit.falseInfo')" value="FALSE_INFO" />
              <el-option :label="t('credit.sublease')" value="SUBLEASE" />
              <el-option :label="t('credit.structure')" value="STRUCTURE" />
              <el-option :label="t('credit.changeUse')" value="CHANGE_USE" />
              <el-option :label="t('credit.vacant')" value="VACANT" />
              <el-option :label="t('credit.illegal')" value="ILLEGAL" />
              <el-option :label="t('credit.arrears')" value="ARREARS" />
              <el-option :label="t('credit.other')" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('credit.measure')" required>
            <el-select v-model="form.sanctionType" style="width:100%" data-testid="f-sanctionType">
              <el-option :label="t('credit.terminate')" value="TERMINATE" />
              <el-option :label="t('credit.banApply')" value="BAN_APPLY" />
              <el-option :label="t('credit.creditPlatform')" value="CREDIT_PLATFORM" />
              <el-option :label="t('credit.fine')" value="FINE" />
              <el-option :label="t('credit.other')" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('credit.banYears')">
            <el-input v-model="form.banYears" type="number" data-testid="f-banYears" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('credit.bizType')">
            <el-select v-model="form.bizType" style="width:100%" clearable>
              <el-option :label="t('credit.exit')" value="EXIT" />
              <el-option :label="t('credit.contract')" value="CONTRACT" />
              <el-option :label="t('credit.application')" value="APPLICATION" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('credit.bizId')">
            <el-input v-model="form.bizId" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item :label="t('credit.desc')">
            <el-input v-model="form.violationDesc" type="textarea" :rows="3"
                      data-testid="f-violationDesc" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('credit.decideOrg')">
            <el-input v-model="form.decideOrgId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('credit.legalNo')">
            <el-input v-model="form.legalDocNo" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item :label="t('credit.reportCredit')">
            <el-switch v-model="form.pushToPlatform" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('credit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('credit.submit') }}</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" :title="t('credit.drawer')" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
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
/** 字段名严格对齐后端 CreditCreateCmd */
const form = reactive({
  personId: '',
  bizType: '',
  bizId: '',
  violationType: 'ARREARS',
  violationDesc: '',
  sanctionType: 'BAN_APPLY',
  banYears: 1,
  decideOrgId: '',
  legalDocNo: '',
  pushToPlatform: false
})

async function load() {
  loading.value = true
  try {
    const d = await req.get('/credits', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  // 必填项与后端 CreditCreateCmd 一致
  const missing = []
  if (!form.personId) missing.push('人员 ID')
  if (!form.violationType) missing.push('违规类型')
  if (!form.sanctionType) missing.push('惩戒措施')
  if (missing.length) { ElMessage.warning('请填写：' + missing.join('、')); return }
  saving.value = true
  try {
    await req.post('/credits', { ...form })
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

async function scanExpired() {
  const r = await req.post('/credits/scan-expired')
  ElMessage.success('扫描完成：' + (r?.count ?? '完成')); load()
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
