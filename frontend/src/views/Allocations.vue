<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">{{ t('alloc.title') }}</h3>
        <el-button type="success" @click="openBatchCreate" data-testid="batch-create">{{ t('alloc.newBatch') }}</el-button>
        <div class="spacer" />
        <el-input v-model="seed" :placeholder="t('alloc.seed')" style="width:200px" />
        <el-button type="primary" @click="load">{{ t('alloc.refresh') }}</el-button>
      </div>

      <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
                :title="t('alloc.tip')" />
      <FilterBar @search="load" @reset="resetQuery">
        <el-select v-model="af.status" :placeholder="t('alloc.status')" clearable style="width:160px"
                   data-testid="alloc-status">
          <el-option :label="t('alloc.draft')" value="DRAFT" />
          <el-option :label="t('alloc.published')" value="PUBLISHED" />
          <el-option :label="t('alloc.signup')" value="SIGNUP" />
          <el-option :label="t('alloc.lottery')" value="LOTTERY" />
          <el-option :label="t('alloc.lotteryDone')" value="LOTTERY_DONE" />
          <el-option :label="t('alloc.selecting')" value="SELECTING" />
          <el-option :label="t('alloc.allocated')" value="ALLOCATED" />
          <el-option :label="t('alloc.closed')" value="CLOSED" />
          <el-option :label="t('alloc.cancelled')" value="CANCELLED" />
        </el-select>
        <el-select v-model="af.orgId" :placeholder="t('alloc.org')" clearable filterable
                   style="width:220px" data-testid="alloc-org">
          <el-option v-for="o in orgOptions" :key="o.id"
                     :label="o.orgName" :value="o.id" />
        </el-select>
      </FilterBar>

      <el-table :empty-text="t('alloc.emptyBatches')" :data="batches" v-loading="loading" border size="small"
                highlight-current-row @row-click="(row) => selectBatch(row)">

        <el-table-column prop="batchNo" :label="t('alloc.batchNo')" width="170" />
        <el-table-column prop="batchName" :label="t('alloc.name')" />
        <el-table-column :label="t('alloc.orgCol')" width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.orgIdName || orgNameOf(row.orgId) }}</template>
        </el-table-column>
        <el-table-column :label="t('alloc.securityType')" width="110">
          <template #default="{ row }">{{ enumLabel('securityType', row.securityType) || row.securityType }}</template>
        </el-table-column>
        <el-table-column prop="batchStatus" :label="t('alloc.statusCol')" width="110">
          <template #default="{ row }">{{ enumLabel('batchStatus', row.batchStatus) || row.batchStatusLabel }}</template>
        </el-table-column>
        <el-table-column prop="houseCount" :label="t('alloc.houseCount')" width="90" />
        <el-table-column prop="applicantCount" :label="t('alloc.applicantCount')" width="100" />
        <el-table-column :label="t('alloc.actions')" width="300" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('alloc.detail') }}</el-button>
            <el-button link type="primary" @click="openAddHouses(row)" data-testid="batch-add-house">{{ t('alloc.addHouses') }}</el-button>
            <el-button v-if="row.batchStatus === 'DRAFT'" link type="success"
                       @click="doTransition(row, 'PUBLISHED')"
                       data-testid="batch-publish">{{ t('alloc.publish') }}</el-button>
            <el-button v-if="row.batchStatus === 'PUBLISHED'" link type="primary"
                       @click="doTransition(row, 'SIGNUP')"
                       data-testid="batch-signup">{{ t('alloc.startSignup') }}</el-button>
            <el-button v-if="row.batchStatus === 'SIGNUP'" link type="warning"
                       @click="doTransition(row, 'LOTTERY')"
                       data-testid="batch-to-lottery">{{ t('alloc.endSignup') }}</el-button>
            <el-dropdown trigger="click" style="margin-left:8px">
              <el-button link type="primary">{{ t('alloc.more') }}</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="['DRAFT','PUBLISHED','SIGNUP'].includes(row.batchStatus)"
                                    @click="doTransition(row, 'CANCELLED')">{{ t('alloc.cancelBatch') }}</el-dropdown-item>
                  <el-dropdown-item @click="viewResults(row)">{{ t('alloc.viewResults') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button link type="primary" @click="runLottery(row)">{{ t('alloc.runLottery') }}</el-button>
            <el-button v-if="['DIRECT','SUPPLEMENT'].includes(row.batchType)
                             && !['DRAFT','CANCELLED','CLOSED'].includes(row.batchStatus)"
                       link type="success" data-testid="batch-manual-alloc"
                       @click="openManual(row)">{{ t('alloc.manualAllocate') }}</el-button>
            <el-button v-if="['LOTTERY_DONE','ALLOCATED','SELECTING'].includes(row.batchStatus)"
                       link type="success" data-testid="batch-gen-alloc"
                       @click="genAllocations(row)">{{ t('alloc.genAllocations') }}</el-button>

          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="page-card">
      <div class="toolbar" style="margin-bottom:12px">
        <h3 style="margin:0">{{ t('alloc.allocTitle') }}</h3>
        <span class="muted" v-if="currentBatch">
          {{ t('alloc.currentBatch', { no: currentBatch.batchNo, name: currentBatch.batchName }) }}
        </span>
        <div class="spacer" />
        <el-button v-if="currentBatch" @click="clearBatch">{{ t('alloc.showAll') }}</el-button>
      </div>
      <el-table :data="allocations" v-loading="loading" border size="small">
        <el-table-column prop="allocationNo" :label="t('alloc.allocNo')" width="170" />
        <el-table-column prop="personId" :label="t('alloc.person')" width="150">
          <template #default="{ row }">{{ row.personName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="phoneMask" :label="t('alloc.phone')" width="130" />
        <el-table-column prop="houseId" :label="t('alloc.house')" width="110">
          <template #default="{ row }">{{ row.houseIdName || row.houseId }}</template>
        </el-table-column>
        <el-table-column prop="allocationStatusLabel" :label="t('alloc.allocStatus')" width="110" />
        <el-table-column prop="lockRemainHours" :label="t('alloc.lockRemain')" width="130" />
        <el-table-column :label="t('alloc.actions')" width="160" fixed="right">
          <template #default="{ row }">
            <el-tag v-if="row.allocationStatus === 'SIGNED'" size="small" type="success">{{ t('alloc.signed') }}</el-tag>
            <el-button v-else link type="success" :disabled="!!row.lockOverdue"
                       @click="sign(row)">{{ t('alloc.goSign') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="resultVisible" :title="t('alloc.resultTitle')" width="700px">
      <el-alert type="info" :closable="false" show-icon
                :title="t('alloc.resultTip')" />
      <el-table :data="results" border size="small" style="margin-top:12px">
        <el-table-column prop="waitingId" :label="t('alloc.waitingId')" width="140">
          <template #default="{ row }">{{ row.waitingId }}</template>
        </el-table-column>
        <el-table-column prop="personId" :label="t('alloc.person')" width="150">
          <template #default="{ row }">{{ row.personName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="phoneMask" :label="t('alloc.phone')" width="130" />
        <el-table-column prop="totalScore" :label="t('alloc.totalScore')" width="100" />
        <el-table-column prop="selectSeq" :label="t('alloc.selectSeq')" width="90" />
        <el-table-column prop="resultType" :label="t('alloc.result')" width="100">
          <template #default="{ row }">{{ row.resultTypeLabel || enumLabel('resultType', row.resultType) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('alloc.detail')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>

    <!-- 新建批次 -->
    <el-dialog v-model="batchCreateVisible" :title="t('alloc.createTitle')" width="620px">
      <el-form :model="bf" label-width="110px">
        <el-form-item :label="t('alloc.batchName')" required>
          <el-input v-model="bf.batchName" :placeholder="t('alloc.batchNameHint')" />
        </el-form-item>
        <el-form-item :label="t('alloc.projectOrg')" required>
          <el-select v-model="bf.orgId" filterable style="width:100%"
                     :placeholder="t('alloc.projectHint')">
            <el-option v-for="o in batchOrgs" :key="o.id" :label="o.orgName" :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('alloc.securityType')" required>
            <el-select v-model="bf.securityType" style="width:100%">
              <el-option :label="t('misc.publicRental')" value="PUBLIC" />
              <el-option :label="t('misc.affordable')" value="AFFORDABLE" />
              <el-option :label="t('misc.talent')" value="TALENT" />
              <el-option :label="t('misc.lowRent')" value="LOW_RENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('alloc.batchType')" required>
            <el-select v-model="bf.batchType" style="width:100%">
              <el-option :label="t('alloc.lotteryType')" value="LOTTERY" />
              <el-option :label="t('alloc.selectType')" value="SELECT" />
              <el-option :label="t('alloc.directType')" value="DIRECT" />
              <el-option :label="t('alloc.supplementType')" value="SUPPLEMENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('alloc.signupStart')">
            <el-date-picker v-model="bf.signupStart" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('alloc.signupEnd')">
            <el-date-picker v-model="bf.signupEnd" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item :label="t('alloc.lotteryTime')">
            <el-date-picker v-model="bf.lotteryTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item :label="t('alloc.house')">
            <div style="width:100%">
              <el-select v-model="bf.houseIds" multiple filterable remote
                         :remote-method="searchHouses" :loading="houseLoading"
                         :placeholder="t('alloc.houseHint')" style="width:100%">
                <el-option v-for="h in houseOptions" :key="h.id"
                           :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'"
                           :value="h.id" />
              </el-select>
              <div class="muted" style="font-size:12px;margin-top:4px">
                {{ t('alloc.selectedHint', { n: (bf.houseIds || []).length }) }}
              </div>
            </div>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item :label="t('alloc.notary')">
            <el-input v-model="bf.notaryInfo" :placeholder="t('alloc.notaryHint')" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="batchCreateVisible = false">{{ t('alloc.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateBatch">{{ t('alloc.create') }}</el-button>
      </template>
    </el-dialog>

    <!-- 批次加房源 -->
    <el-dialog v-model="addHouseVisible" :title="t('alloc.manageHouses')" width="900px">
      <div class="toolbar" style="margin-bottom:8px">
        <span>{{ t('alloc.batchLabel', { no: addHouseBatch?.batchNo, name: addHouseBatch?.batchName }) }}</span>
        <div class="spacer" />
        <el-input v-model="houseKeyword" :placeholder="t('alloc.searchHouse')" clearable style="width:200px"
                  @keyup.enter="loadCandidateHouses" />
        <el-button type="primary" @click="loadCandidateHouses">{{ t('alloc.searchHouse') }}</el-button>
      </div>

      <h4 style="margin:8px 0">{{ t('alloc.addable', { org: addHouseBatch?.orgIdName || t('alloc.addableDefault') }) }}</h4>
      <el-table :data="candidateHouses" v-loading="houseLoading" border size="small"
                max-height="240" @selection-change="(rows) => selectedHouses = rows">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="houseCode" :label="t('alloc.houseCode')" width="150" />
        <el-table-column prop="houseName" :label="t('alloc.houseName')" show-overflow-tooltip />
        <el-table-column prop="area" :label="t('alloc.area')" width="100" />
        <el-table-column :label="t('alloc.status')" width="100">
          <template #default="{ row }">{{ enumLabel('houseStatus', row.houseStatus) || row.houseStatus }}</template>
        </el-table-column>
      </el-table>

      <h4 style="margin:14px 0 8px">{{ t('alloc.added', { n: batchHouses.length }) }}</h4>
      <el-table :data="batchHouses" border size="small" max-height="220">
        <el-table-column prop="houseCode" :label="t('alloc.houseCode')" width="150" />
        <el-table-column prop="houseName" :label="t('alloc.houseName')" show-overflow-tooltip />
        <el-table-column prop="inPoolStatus" :label="t('alloc.poolStatus')" width="110" />
        <el-table-column :label="t('alloc.actions')" width="100">
          <template #default="{ row }">
            <el-button link type="danger" :disabled="row.inPoolStatus !== 'AVAILABLE'"
                       @click="removeHouse(row)">{{ t('alloc.remove') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="addHouseVisible = false">{{ t('alloc.close') }}</el-button>
        <el-button type="primary" :loading="saving" :disabled="!selectedHouses.length"
                   @click="doAddSelectedHouses">{{ t('alloc.addSelected', { n: selectedHouses.length }) }}</el-button>
      </template>
    </el-dialog>

    <!-- 直接/补充配租：指定人员与房源 -->
    <el-dialog v-model="manualVisible" :title="t('alloc.manualAllocateTitle')" width="620px">
      <el-form label-width="110px">
        <el-form-item :label="t('alloc.batchLabel', { no: manualBatch?.batchNo, name: manualBatch?.batchName })" />
        <el-form-item :label="t('alloc.manualPerson')" required>
          <PersonPicker v-model="manualForm.personId" width="100%" />
        </el-form-item>
        <el-form-item :label="t('alloc.manualHouse')" required>
          <el-select v-model="manualForm.houseId" filterable style="width:100%"
                     :placeholder="t('alloc.manualHouseHint')">
            <el-option v-for="h in manualHouses" :key="h.houseId"
                       :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'"
                       :value="String(h.houseId)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('alloc.manualPlanStart')">
          <el-date-picker v-model="manualForm.planRentStart" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('alloc.manualPlanEnd')">
          <el-date-picker v-model="manualForm.planRentEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="manualVisible = false">{{ t('alloc.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" :disabled="!manualForm.personId || !manualForm.houseId"
                   @click="doManualAllocate">{{ t('alloc.manualSubmit') }}</el-button>
      </template>
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
import { ref, reactive, onMounted, watch } from 'vue'
import DetailView from '@/components/DetailView.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { allocationApi } from '@/api/modules'
import req from '@/api/request'
import FilterBar from '@/components/FilterBar.vue'
import PersonPicker from '@/components/PersonPicker.vue'

const loading = ref(false)
const batches = ref([])
const currentBatch = ref(null)
const allocations = ref([])
const results = ref([])
const resultVisible = ref(false)
const seed = ref('20261019')
/** 批次筛选（后端 /allocations/batches 支持 status / orgId） */
const af = reactive({ status: '', orgId: '' })

/** 清空筛选条件 */
function resetQuery() {
  af.status = ''
  af.orgId = ''
  load()
}

/** 配租单：默认全部，选中批次后按批次过滤 */
async function loadAllocations() {
  const a = await allocationApi.allocations({
    pageNum: 1, pageSize: 100,
    batchId: currentBatch.value ? currentBatch.value.id : undefined
  })
  allocations.value = a.rows || []
}

function selectBatch(row) {
  currentBatch.value = row
  loadAllocations()
}

function clearBatch() {
  currentBatch.value = null
  loadAllocations()
}

async function load() {
  loading.value = true
  try {
    const b = await allocationApi.batches({
      pageNum: 1, pageSize: 50,
      status: af.status || undefined,
      orgId: af.orgId || undefined
    })
    batches.value = b.rows || []
    await loadAllocations()
  } finally {
    loading.value = false
  }
}

async function runLottery(row) {
  const houses = await batchHouseCount(row.id)
  // 参与人数以批次为准（同组织同类型轮候池），没有再回退全局统计
  const waiting = Number(row.applicantCount || 0) || await waitingCountOf(row.securityType)
  if (!waiting) {
    ElMessage.warning(t('alloc.noWaiting'))
    return
  }
  if (!houses) {
    ElMessage.warning(t('alloc.noHouses'))
    return
  }
  try {
    await ElMessageBox.confirm(
      t('alloc.lotteryConfirm', { waiting, houses }),
      t('alloc.lotteryTitle'),
      { type: 'warning', confirmButtonText: t('alloc.startLottery'), cancelButtonText: t('alloc.cancel') })
  } catch (e) { return }
  try {
    await req.post('/allocation/lottery', { batchId: row.id, seed: seed.value || undefined })
    ElMessage.success(t('alloc.lotteryDone'))
    load()
    viewResults(row)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('alloc.lotteryFailed'))
  }
}

async function viewResults(row) {
  results.value = await allocationApi.results(row.id)
  resultVisible.value = true
}

async function sign(row) {
  await ElMessageBox.confirm(
    t('alloc.signConfirm'),
    t('alloc.signTitle'), { type: 'warning' })
  try {
    await allocationApi.sign(row.id, {})
    ElMessage.success(t('alloc.signSuccess'))
    load()
  } catch (e) {
    // 拦截器已提示（常见：公示未结束）
  }
}


/** 新建批次 / 批次加房源（此前只能看列表，无法从界面建批次） */
const batchCreateVisible = ref(false)
const addHouseVisible = ref(false)
const addHouseBatch = ref(null)
const houseIdsText = ref('')
const bf = reactive({ batchName: '', orgId: '', houseIds: [], securityType: 'PUBLIC',
  batchType: 'LOTTERY', signupStart: '', signupEnd: '', lotteryTime: '',
  notaryInfo: '' })
const orgOptions = ref([])
const saving = ref(false)
const batchOrgs = ref([])


/** 组织列表（名称用于筛选与批次下拉） */
async function loadOrgOptions() {
  if (orgOptions.value.length) return
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    const rows = (d && d.rows) || (Array.isArray(d) ? d : [])
    orgOptions.value = rows.map((o) => ({ id: o.id, orgName: o.orgName }))
  } catch (e) { /* 忽略 */ }
}

function orgNameOf(id) {
  const hit = orgOptions.value.find((o) => String(o.id) === String(id))
  return hit ? hit.orgName : (id || '—')
}

const houseOptions = ref([])
const houseLoading = ref(false)

/** 组织下「待分配」房源，支持关键字搜索 */
async function searchHouses(keyword) {
  if (!bf.orgId) return
  houseLoading.value = true
  try {
    const d = await req.get('/houses', {
      params: { pageNum: 1, pageSize: 100, orgId: bf.orgId,
        houseStatus: 'PENDING_ALLOC', keyword: keyword || undefined }
    })
    houseOptions.value = (d && d.rows) || []
  } catch (e) { houseOptions.value = [] } finally { houseLoading.value = false }
}

async function openBatchCreate() {
  Object.assign(bf, { batchName: '', orgId: '', houseIds: [], securityType: 'PUBLIC',
    batchType: 'LOTTERY', signupStart: '', signupEnd: '', lotteryTime: '', notaryInfo: '' })
  houseOptions.value = []
  batchCreateVisible.value = true
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    const rows = (d && d.rows) || (Array.isArray(d) ? d : [])
    batchOrgs.value = rows.map((o) => ({ id: String(o.id), orgName: o.orgName }))
    if (!orgOptions.value.length) orgOptions.value = batchOrgs.value
  } catch (e) { batchOrgs.value = [] }
  if (!bf.orgId && batchOrgs.value.length) {
    bf.orgId = batchOrgs.value[0].id
    searchHouses('')
  }
}

async function doCreateBatch() {
  if (!bf.batchName) { ElMessage.warning(t('alloc.batchNameRequired')); return }
  if (!bf.orgId) { ElMessage.warning(t('alloc.orgRequired')); return }
  const ids = (bf.houseIds || []).map(String)
  saving.value = true
  try {
    await req.post('/allocation/batches', {
      batchName: bf.batchName,
      orgId: bf.orgId,
      securityType: bf.securityType,
      batchType: bf.batchType,
      signupStart: bf.signupStart || null,
      signupEnd: bf.signupEnd || null,
      lotteryTime: bf.lotteryTime || null,
      houseIds: ids.length ? ids : null,
      notaryInfo: bf.notaryInfo || null
    })
    ElMessage.success(t('alloc.batchCreated'))
    batchCreateVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || e?.message || t('alloc.createFailed'))
  } finally { saving.value = false }
}

function openAddHouses(row) {
  addHouseBatch.value = row
  houseIdsText.value = ''
  houseKeyword.value = ''
  selectedHouses.value = []
  candidateHouses.value = []
  addHouseVisible.value = true
  loadBatchHouses().then(loadCandidateHouses)
}

const houseKeyword = ref('')
const candidateHouses = ref([])
const batchHouses = ref([])
const selectedHouses = ref([])

/** 可选房源：本批次组织下的待分配房源 */
async function loadCandidateHouses() {
  if (!addHouseBatch.value) return
  houseLoading.value = true
  try {
    const d = await req.get('/houses', {
      params: { pageNum: 1, pageSize: 100, orgId: addHouseBatch.value.orgId,
        houseStatus: 'PENDING_ALLOC', keyword: houseKeyword.value || undefined }
    })
    const inBatch = new Set(batchHouses.value.map((x) => String(x.houseId)))
    candidateHouses.value = (d.rows || []).filter((h) => !inBatch.has(String(h.id)))
  } catch (e) { candidateHouses.value = [] } finally { houseLoading.value = false }
}

/** 已加入本批次的房源明细 */
async function loadBatchHouses() {
  if (!addHouseBatch.value) return
  try {
    batchHouses.value = await req.get('/allocation/batches/' + addHouseBatch.value.id + '/houses/detail')
  } catch (e) { batchHouses.value = [] }
}

/** 加入所选房源 */
async function doAddSelectedHouses() {
  const ids = selectedHouses.value.map((h) => String(h.id))
  if (!ids.length) { ElMessage.warning(t('alloc.selectHouses')); return }
  saving.value = true
  try {
    const n = await req.post('/allocation/batches/' + addHouseBatch.value.id + '/houses', { houseIds: ids })
    ElMessage.success(t('alloc.addedCount', { n: n == null ? ids.length : n }))
    selectedHouses.value = []
    await loadBatchHouses(); await loadCandidateHouses(); load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('alloc.addFailed'))
  } finally { saving.value = false }
}

/** 移除已加入房源 */
async function removeHouse(row) {
  try {
    await ElMessageBox.confirm(t('alloc.removeConfirm', { code: row.houseCode || row.houseId }), t('alloc.removeTitle'),
      { type: 'warning' })
  } catch (e) { return }
  try {
    const n = await req.post('/allocation/batches/' + addHouseBatch.value.id + '/houses/remove',
      { houseIds: [String(row.houseId)] })
    ElMessage.success(t('alloc.removed', { n: n || 0 }))
    await loadBatchHouses(); await loadCandidateHouses(); load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('alloc.removeFailed'))
  }
}

async function doAddHouses() {
  const ids = houseIdsText.value.split(/[,，\s]+/).map((x) => x.trim()).filter(Boolean)
  if (!ids.length) { ElMessage.warning('请填写房源 ID'); return }
  saving.value = true
  try {
    await req.post(`/allocation/batches/${addHouseBatch.value.id}/houses`, { houseIds: ids })
    ElMessage.success(`已加入 ${ids.length} 个房源`)
    addHouseVisible.value = false
    load()
  } finally { saving.value = false }
}


/** 批次状态流转：发布 → 报名 → 摇号 */
const TRANSITION_TIP = {
  PUBLISHED: t('alloc.transPublish'),
  SIGNUP: t('alloc.transSignup'),
  LOTTERY: t('alloc.transLottery'),
  CANCELLED: t('alloc.transCancel')
}

const manualVisible = ref(false)
const manualBatch = ref(null)
const manualHouses = ref([])
const manualForm = reactive({ personId: null, houseId: '', planRentStart: '', planRentEnd: '' })

async function openManual(row) {
  manualBatch.value = row
  manualForm.personId = null
  manualForm.houseId = ''
  manualForm.planRentStart = ''
  manualForm.planRentEnd = ''
  manualHouses.value = []
  manualVisible.value = true
  try {
    const list = await req.get('/allocation/batches/' + row.id + '/houses/detail')
    manualHouses.value = (list || []).filter((h) => h.inPoolStatus === 'AVAILABLE')
  } catch (e) { manualHouses.value = [] }
}

async function doManualAllocate() {
  if (!manualForm.personId || !manualForm.houseId) {
    ElMessage.warning(t('alloc.manualRequired'))
    return
  }
  saving.value = true
  try {
    await req.post('/allocation/allocations', {
      batchId: manualBatch.value.id,
      personId: manualForm.personId,
      houseId: manualForm.houseId,
      planRentStart: manualForm.planRentStart || null,
      planRentEnd: manualForm.planRentEnd || null
    })
    ElMessage.success(t('alloc.manualSuccess'))
    manualVisible.value = false
    load(); loadAllocations()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('alloc.manualFailed'))
  } finally { saving.value = false }
}

/** 摇号完成 → 按中签顺序生成配租单 */
async function genAllocations(row) {
  try {
    await ElMessageBox.confirm(
      t('alloc.genConfirm'),
      t('alloc.genTitle'), { type: 'warning' })
  } catch (e) { return }
  try {
    const r = await req.post('/allocation/batches/' + row.id + '/generate-allocations')
    ElMessage.success(r?.message || t('alloc.genDone', { n: r?.generated || 0 }))
    currentBatch.value = row
    await loadAllocations(); load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('alloc.genFailed'))
  }
}

/** 轮候池人数（按保障类型统计，用于摇号前提示） */
async function waitingCountOf(securityType) {
  try {
    const d = await req.get('/allocation/waiting', { params: { pageNum: 1, pageSize: 1, securityType } })
    return Number((d && d.total) || 0)
  } catch (e) { return 0 }
}

/** 批次房源套数 */
async function batchHouseCount(batchId) {
  try {
    const d = await req.get('/allocation/batches/' + batchId + '/houses')
    return Array.isArray(d) ? d.length : Number((d && d.total) || 0)
  } catch (e) { return 0 }
}
async function doTransition(row, target) {
  try {
    await ElMessageBox.confirm(TRANSITION_TIP[target] || '确认变更状态？', '状态变更',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' })
  } catch (e) { return }
  try {
    await req.post(`/allocation/batches/${row.id}/status`, { batchStatus: target })
    ElMessage.success(t('alloc.statusUpdated'))
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '状态变更失败')
    load()   // 刷新列表，避免前端状态与后端不一致
  }
}

watch(() => bf.orgId, (v) => {
  bf.houseIds = []
  houseOptions.value = []
  if (v) searchHouses('')
})

onMounted(() => { load(); loadOrgOptions() })
</script>
