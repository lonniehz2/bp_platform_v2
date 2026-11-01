<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="query.applicationStatus" :placeholder="t('application.status')" clearable
                   style="width:150px" @change="load">
          <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
        </el-select>
        <PersonPicker v-model="query.personId" width="260px" testid="app-person-picker" />
        <el-button type="primary" @click="load">{{ t('application.search') }}</el-button>
        <el-button @click="resetQuery">{{ t('application.reset') }}</el-button>
        <div class="spacer" />
        <el-button type="success" @click="openCreate">
          <el-icon><Plus /></el-icon>{{ t('application.create') }}
        </el-button>
      </div>

      <el-table :empty-text="t('application.empty')" :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="applicationNo" :label="t('application.no')" width="160" />
        <el-table-column prop="personName" :label="t('application.applicant')" width="110">
        <template #default="{ row }">
          {{ row.personName || row.personId }}
        </template>
      </el-table-column>
        <el-table-column prop="securityType" :label="t('application.securityType')" width="120">
          <template #default="{ row }">{{ row.securityTypeLabel || enumLabel('securityType', row.securityType) }}</template>
        </el-table-column>
        <el-table-column prop="familySize" :label="t('application.familySize')" width="90" />
        <el-table-column prop="incomePerCapita" :label="t('application.income')" width="110" />
        <el-table-column prop="applicationStatusLabel" :label="t('application.statusCol')" width="100">
          <template #default="{ row }">
            <el-tag :type="tagOf(row.applicationStatus)" size="small">
              {{ row.applicationStatusLabel || row.applicationStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="currentNode" :label="t('application.node')" width="100">
        <template #default="{ row }">{{ row.currentNodeLabel || enumLabel('currentNode', row.currentNode) }}</template>
      </el-table-column>
        <el-table-column prop="applyTime" :label="t('application.applyTime')" width="170" />
        <el-table-column :label="t('application.actions')" width="290" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('application.detail') }}</el-button>
            <el-button v-if="row.applicationStatus === 'SUBMITTED'" link type="success"
                       @click="accept(row)" data-testid="row-accept">{{ t('application.accept') }}</el-button>
            <el-button v-if="row.applyChannel === 'OFFLINE'
                       && ['SUBMITTED','ACCEPTED','REVIEWING'].includes(row.applicationStatus)"
                       link type="warning" data-testid="row-offline-pass"
                       @click="offlinePass(row)">{{ t('appX.offlinePass') }}</el-button>
            <el-button v-if="canReview(row)" link type="primary"
                       @click="openReview(row)">{{ t('application.review') }}</el-button>
            <el-button v-if="row.applicationStatus === 'SUPPLEMENT'" link type="warning"
                       data-testid="row-supplement" @click="supplement(row)">补件完成</el-button>
            <el-button link @click="openRecords(row)">{{ t('application.records') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                     :total="+total || 0" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />
    </div>

    <!-- 新建申请 -->
    <el-dialog v-model="createVisible" :title="t('application.createTitle')" width="560px">
      <el-form :model="form" label-width="110px">
        <el-form-item :label="t('application.org')">
          <OrgSelect v-model="form.orgId" width="100%" testid="app-org" />
        </el-form-item>
        <el-form-item :label="t('application.applicantId')">
          <PersonPicker v-model="form.personId" width="240px" testid="person-picker" />
        </el-form-item>
        <el-form-item :label="t('application.securityType')">
          <el-select v-model="form.securityType">
            <el-option v-for="o in securityTypeOptions" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('application.mode')">
          <el-select v-model="form.securityMode">
            <el-option :label="t('appX.houseAlloc')" value="HOUSE" />
            <el-option :label="t('appX.subsidy')" value="SUBSIDY" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('application.channel')">
          <el-select v-model="form.applyChannel">
            <el-option :label="t('appX.online')" value="ONLINE" />
            <el-option :label="t('appX.offline')" value="OFFLINE" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('application.familySize')">
          <el-input v-model.number="form.familySize" />
        </el-form-item>
        <el-form-item :label="t('application.familyIncome')">
          <el-input v-model.number="form.declaredIncome" />
        </el-form-item>
        <el-alert type="warning" :closable="false" show-icon
                  :title="t('appX.submitTip')" />
        <el-form-item :label="t('application.promise')" style="margin-top:8px">
          <el-switch v-model="form.complianceCommitFlag" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item :label="t('application.agree')">
          <el-switch v-model="form.dataShareAgreeFlag" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('application.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="save">{{ t('application.submit') }}</el-button>
      </template>
    </el-dialog>

    <!-- 审核 -->
    <el-dialog v-model="reviewVisible" :title="t('application.reviewTitle')" width="560px">
      <el-descriptions :column="2" border size="small" style="margin-bottom:14px">
        <el-descriptions-item :label="t('appX.appNo')">{{ current?.applicationNo }}</el-descriptions-item>
        <el-descriptions-item :label="t('appX.applicant')">{{ current?.personId }}</el-descriptions-item>
        <el-descriptions-item :label="t('appX.securityType')">{{ enumLabel('securityType', current?.securityType) }}</el-descriptions-item>
        <el-descriptions-item :label="t('appX.status')">{{ current?.applicationStatusLabel }}</el-descriptions-item>
      </el-descriptions>
      <el-alert type="info" :closable="false" show-icon
                :title="t('appX.approveTip')" />
      <el-form :model="reviewForm" label-width="90px" style="margin-top:12px">
        <el-form-item :label="t('application.stage')">
          <el-select v-model="reviewForm.stage" disabled>
            <el-option :label="t('appX.acceptStage')" value="ACCEPT" />
            <el-option :label="t('appX.formStage')" value="FORM" />
            <el-option :label="t('appX.jointStage')" value="JOINT" />
            <el-option :label="t('appX.finalStage')" value="FINAL" />
          </el-select>
          <div class="muted" style="font-size:12px;margin-left:8px">
            {{ t('appX.stageHint') }}
          </div>
        </el-form-item>
        <el-form-item :label="t('application.result')">
          <el-radio-group v-model="reviewForm.result">
            <el-radio value="PASS">{{ t('application.pass') }}</el-radio>
            <el-radio value="REJECT">{{ t('application.reject') }}</el-radio>
            <el-radio value="SUPPLEMENT">{{ t('application.needSupplement') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('application.opinion')">
          <el-input v-model="reviewForm.opinion" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">{{ t('appX.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doReview">{{ t('appX.submit') }}</el-button>
      </template>
    </el-dialog>

    <!-- 轨迹 -->
    <el-drawer v-model="recordsVisible" :title="t('application.recordsTitle')" size="520px">
      <el-timeline>
        <el-timeline-item v-for="r in records" :key="r.id"
                          :timestamp="r.reviewTime" placement="top">
          <b>{{ r.reviewStage }} · {{ r.reviewResult }}</b>
          <div class="muted">{{ r.reviewUserName }} — {{ r.reviewOpinion }}</div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!records.length" :description="t('application.noRecords')" />
    </el-drawer>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('application.detailTitle')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import DetailView from '@/components/DetailView.vue'
import PersonPicker from '@/components/PersonPicker.vue'
import OrgSelect from '@/components/OrgSelect.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { applicationApi } from '@/api/modules'
import { useDict } from '@/composables/useDict'

const statuses = ['DRAFT', 'SUBMITTED', 'ACCEPTED', 'REVIEWING', 'SUPPLEMENT',
  'APPROVED', 'REJECTED', 'CANCELLED']

// 保障类型走系统字典（可后台维护，无需改前端）
const { options: securityTypeOptions } = useDict('SECURITY_TYPE', [
  { value: 'PUBLIC', label: t('misc.publicRental') },
  { value: 'AFFORDABLE', label: t('misc.affordable') },
  { value: 'TALENT', label: t('misc.talent') },
  { value: 'LOW_RENT', label: t('misc.lowRent') }
])

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, applicationStatus: '', personId: '' })

const createVisible = ref(false)
const form = reactive({
  orgId: null, personId: null, securityType: 'PUBLIC', securityMode: 'HOUSE',
  applyChannel: 'ONLINE', familySize: 1, declaredIncome: null,
  complianceCommitFlag: 1, dataShareAgreeFlag: 1
})

const reviewVisible = ref(false)
const current = ref(null)
const reviewForm = reactive({ stage: 'FINAL', result: 'PASS', opinion: '' })

const recordsVisible = ref(false)
const records = ref([])

function tagOf(s) {
  return ({ APPROVED: 'success', REJECTED: 'danger', SUPPLEMENT: 'warning',
    REVIEWING: 'primary', ACCEPTED: 'info' })[s] || 'info'
}

async function load() {
  loading.value = true
  try {
    const data = await applicationApi.page({
      pageNum: query.pageNum, pageSize: query.pageSize,
      // 后端参数名是 status（不是 applicationStatus），传错会被静默忽略
      status: query.applicationStatus || undefined,
      personId: query.personId || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  createVisible.value = true
}

async function save() {
  const missing = []
  if (!form.personId) missing.push(t('appX.requiredApplicant'))
  if (!form.orgId) missing.push(t('appX.requiredOrg'))
  if (!form.houseId) missing.push(t('appX.requiredHouse'))
  if (!form.securityType) missing.push(t('appX.requiredSecurity'))
  if (missing.length) {
    ElMessage.warning(t('appX.fill', { fields: missing.join(', ') }))
    return
  }
  saving.value = true
  try {
    await applicationApi.create({ ...form })
    ElMessage.success(t('appX.created'))
    createVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}


/** 只有已受理/审核中/补件状态可以审核 */
function canReview(row) {
  return ['ACCEPTED', 'REVIEWING', 'SUPPLEMENT'].includes(row.applicationStatus)
}

/** 受理：已提交 → 已受理 */
async function accept(row) {
  try {
    await req.post(`/applications/${row.id}/accept`, {})
    ElMessage.success(t('appX.accepted'))
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('appX.acceptFailed'))
  }
}

function openReview(row) {
  current.value = row
  reviewForm.stage = stageOfNode(row.currentNode)
  reviewForm.result = 'PASS'
  reviewForm.opinion = ''
  reviewVisible.value = true
}

/** 当前环节 → 审核阶段（默认值，锁定不可跳级） */
function stageOfNode(node) {
  return ['ACCEPT', 'FORM', 'JOINT', 'FINAL'].includes(node) ? node : 'FINAL'
}

/** 线下受理通过：先受理（如未受理），再做终审通过 */
async function offlinePass(row) {
  await ElMessageBox.confirm(
    t('appX.offlineConfirm'),
    t('appX.offlineTitle'), { type: 'warning' })
  saving.value = true
  try {
    if (row.applicationStatus === 'SUBMITTED') {
      await req.post(`/applications/${row.id}/accept`, {})
    }
    await applicationApi.review(row.id, {
      stage: 'FINAL',
      result: 'PASS',
      opinion: row.offlineRemark || t('appX.offlineRemark')
    })
    ElMessage.success(t('appX.offlinePassed'))
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('appX.offlineFailed'))
  } finally { saving.value = false }
}

async function doReview() {
  saving.value = true
  try {
    await applicationApi.review(current.value.id, { ...reviewForm })
    ElMessage.success(t('appX.reviewed'))
    reviewVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('appX.reviewFailed'))
  } finally {
    saving.value = false
  }
}

/** 补件完成：把申请从「需补件」推回「审核中」 */
async function supplement(row) {
  const { value } = await ElMessageBox.prompt(
    t('appX.supplementConfirm'), t('appX.supplementTitle'), { inputValue: '' })
  try {
    await applicationApi.resubmit(row.id, { remark: value || undefined })
    ElMessage.success(t('appX.supplementDone'))
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('appX.supplementFailed'))
  }
}

async function openRecords(row) {
  try {
    records.value = await applicationApi.reviews(row.id)
  } catch (e) {
    records.value = []
    ElMessage.error(e?.response?.data?.message || t('appX.timelineFailed'))
  }
  recordsVisible.value = true
}

const query0 = JSON.parse(JSON.stringify(query))
function resetQuery() {
  Object.assign(query, query0)
  load()
}

// 从待办中心「待审申请」点进来时带 pending=1，这里把状态筛选设为待审
if (/pending=1/.test(window.location.hash)) {
  query.applicationStatus = 'SUBMITTED'
}
onMounted(load)
</script>
