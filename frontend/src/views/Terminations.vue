<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('termination.title') }}</h3>
      <el-tag size="small" type="info">{{ t('misc2.termTag') }}</el-tag>
      <div class="spacer" />
      <el-button type="success" @click="openCreate">{{ t('termination.create') }}</el-button>
      <el-button @click="load">{{ t('termination.refresh') }}</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon
              :title="t('misc2.termTip')"
              style="margin-bottom:12px" />

    <FilterBar @search="resetAndLoad" @reset="resetQuery">
      <el-select v-model="tf.status" :placeholder="t('termination.status')" clearable style="width:160px"
                 data-testid="term-status">
        <el-option :label="t('termination.applying')" value="APPLYING" />
        <el-option :label="t('termination.approving')" value="APPROVING" />
        <el-option :label="t('termination.approved')" value="APPROVED" />
        <el-option :label="t('termination.completed')" value="COMPLETED" />
        <el-option :label="t('termination.rejected')" value="REJECTED" />
        <el-option :label="t('termination.cancelled')" value="CANCELLED" />
      </el-select>
      <template #more>
        <OrgSelect v-model="tf.orgId" width="200px" testid="term-org" />
        <HouseSelect v-model="tf.houseId" width="200px" testid="term-house" />
        <el-input v-model="tf.keyword" :placeholder="t('termination.keyword')" clearable
                  style="width:200px" data-testid="term-keyword" />
        <ContractSelect v-model="tf.contractId" width="200px" testid="contract-select" />
        <el-select v-model="tf.type" :placeholder="t('termination.type')" clearable style="width:160px">
          <el-option :label="t('termination.agreement')" value="AGREEMENT" />
          <el-option :label="t('termination.breach')" value="BREACH" />
          <el-option :label="t('termination.expire')" value="EXPIRE" />
        </el-select>
      </template>
    </FilterBar>

    <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('misc.emptyDefault')">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="terminationNo" :label="t('termination.no')" width="170" />
      <el-table-column prop="contractId" :label="t('termination.contract')" width="130">
        <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
      </el-table-column>
      <el-table-column prop="orgName" :label="t('termination.org')" width="150" />
      <el-table-column prop="houseName" :label="t('termination.house')" width="140" />
      <el-table-column prop="lesseeName" :label="t('termination.lessee')" width="110" />
      <el-table-column :label="t('termination.lease')" width="180">
        <template #default="{ row }">{{ row.leaseStart }} ~ {{ row.leaseEnd }}</template>
      </el-table-column>
      <el-table-column :label="t('termination.rent')" width="100" >
          <template #default="{ row }">{{ $money(row.monthlyRent) }}</template>
        </el-table-column>
      <el-table-column :label="t('termination.deposit')" width="100" >
          <template #default="{ row }">{{ $money(row.depositAmount) }}</template>
        </el-table-column>
      <el-table-column prop="terminationType" :label="t('termination.type')" width="120">
        <template #default="{ row }">{{ row.terminationTypeLabel || enumLabel('terminationType', row.terminationType) }}</template>
      </el-table-column>
      <el-table-column :label="t('termination.exitDate')" width="150">
        <template #default="{ row }">
          <span v-if="row.actualExitDate">{{ row.actualExitDate }}</span>
          <span v-else-if="row.planExitDate" class="muted">
            {{ t('misc2.plan', { date: row.planExitDate }) }}
          </span>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
      <el-table-column prop="terminationStatus" :label="t('termination.statusCol')" width="130">
        <template #default="{ row }">
          <el-tag size="small" :type="row.terminationStatus === 'COMPLETED' ? 'success'
            : (row.terminationStatus === 'REJECTED' ? 'danger' : 'warning')">
            {{ row.terminationStatusLabel || enumLabel('terminationStatus', row.terminationStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('termination.actions')" width="320" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('termination.detail') }}</el-button>
          <el-dropdown style="margin:0 8px">
            <el-button link type="primary">{{ t('termination.more') }}</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="doSubmit(row)">{{ t('termination.submit') }}</el-dropdown-item>
                <el-dropdown-item @click="approve(row)">{{ t('misc2.approve') }}</el-dropdown-item>
                <el-dropdown-item @click="doReject(row)">{{ t('termination.reject') }}</el-dropdown-item>
                <el-dropdown-item @click="doCancel(row)">{{ t('misc2.cancel') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button v-if="row.inspectStatus && row.inspectStatus !== 'PENDING'"
                     link type="success" @click="openDetail(row)">{{ t('misc2.inspected') }}</el-button>
          <el-button v-else link @click="openInspect(row)">{{ t('termination.inspect') }}</el-button>
          <el-button v-if="row.settleStatus === 'SETTLED'" link type="success"
                     @click="openDetail(row)">{{ t('misc2.settleBill') }}</el-button>
          <el-button v-else link type="primary" @click="openEnergy(row)">{{ t('termination.energy') }}</el-button>
          <el-button v-if="row.settleStatus !== 'SETTLED'" link type="warning" :disabled="!row.inspectStatus
                     || row.inspectStatus === 'PENDING'" @click="openSettle(row)">{{ t('misc2.settle') }}</el-button>
          <el-button v-if="row.settleStatus === 'SETTLED'" link type="success"
                     @click="doComplete(row)">{{ t('misc2.complete') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <!-- 发起退租 TerminationCreateCmd -->
    <el-dialog v-model="createVisible" :title="t('termination.createTitle')" width="560px">
      <el-form :model="c" label-width="120px">
        <el-form-item :label="t('termination.person')" required>
          <PersonPicker v-model="c.personId" width="260px" testid="person-picker" />
        </el-form-item>
        <el-form-item :label="t('termination.origContract')">
          <el-input :model-value="auto.contractNo || c.contractId" disabled />
        </el-form-item>
        <el-form-item :label="t('termination.origHouse')">
          <el-input :model-value="auto.houseName || c.houseId" disabled />
        </el-form-item>
        <el-form-item :label="t('termination.org')">
          <el-input :model-value="auto.orgName" disabled />
        </el-form-item>
        <el-form-item :label="t('termination.leaseTerm')">
          <el-input :model-value="auto.leaseStart + ' ~ ' + auto.leaseEnd" disabled />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('termination.rent')">
            <el-input :model-value="auto.monthlyRent" disabled /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('termination.deposit')">
            <el-input :model-value="auto.depositAmount" disabled /></el-form-item></el-col>
        </el-row>
        <el-alert v-if="c.personId && !auto.contractNo" type="warning" :closable="false"
                  :title="t('misc6.noContract')" style="margin-bottom:8px" />
        <el-form-item :label="t('misc6.terminationType')">
          <el-select v-model="c.terminationType" style="width:100%">
            <el-option :label="t('termination.normal')" value="NORMAL" />
            <el-option :label="t('termination.expel')" value="EXPEL" />
            <el-option :label="t('termination.expireNotRenew')" value="EXPIRE" />
            <el-option :label="t('termination.exchange')" value="EXCHANGE" />
            <el-option :label="t('termination.other')" value="OTHER" />
          </el-select></el-form-item>
        <el-form-item :label="t('termination.planExit')">
          <el-date-picker v-model="c.planExitDate" type="date"
                          value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item :label="t('termination.exitReason')">
          <el-input v-model="c.exitReason" type="textarea" :rows="2" /></el-form-item>
        <el-form-item :label="t('termination.transitionMonths')">
          <el-input v-model.number="c.transitionMonths" :placeholder="t('misc6.default3')" /></el-form-item>
        <el-form-item :label="t('misc6.transitionMultiplier')">
          <el-input v-model.number="c.transitionRentMultiplier" :placeholder="t('misc6.default15')" />
        </el-form-item>
        <el-form-item :label="t('misc6.relocationMonths')">
          <el-input v-model.number="c.relocationMonths" :placeholder="t('misc6.relocationHint')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('termination.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">{{ t('termination.submit') }}</el-button>
      </template>
    </el-dialog>

    <!-- 查验 InspectCmd -->
    <el-dialog v-model="inspectVisible" :title="t('terminationX.inspectTitle')" width="500px">
      <el-form :model="ins" label-width="120px">
        <el-form-item :label="t('terminationX.inspectResult')">
          <el-select v-model="ins.inspectStatus" style="width:100%">
            <el-option :label="t('terminationX.pass')" value="PASS" />
            <el-option :label="t('terminationX.repair')" value="REPAIR" />
            <el-option :label="t('terminationX.damaged')" value="DAMAGED" />
          </el-select></el-form-item>
        <el-form-item :label="t('terminationX.inspectNote')">
          <el-input v-model="ins.inspectResult" type="textarea" :rows="2" /></el-form-item>
        <el-form-item :label="t('terminationX.damageAmount')">
          <el-input v-model.number="ins.damageAmount" /></el-form-item>
        <el-form-item :label="t('terminationX.photoUrl')">
          <el-input v-model="ins.inspectImages" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inspectVisible = false">{{ t('terminationX.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doInspect">{{ t('terminationX.submit') }}</el-button>
      </template>
    </el-dialog>

    <!-- 退租能耗即时结算 -->
    <el-dialog v-model="energyVisible" :title="t('terminationX.energyTitle')" width="480px">
      <el-alert type="warning" :closable="false" show-icon
                :title="t('terminationX.energyTip')" />
      <el-form :model="ef" label-width="100px" style="margin-top:10px">
        <el-form-item :label="t('terminationX.meter')" required>
          <el-select v-model="ef.meterPointId" filterable style="width:100%">
            <el-option v-for="p in energyPoints" :key="p.id"
                       :label="p.meterName || p.id" :value="String(p.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('terminationX.currentReading')" required>
          <el-input v-model.number="ef.reading" />
        </el-form-item>
        <el-form-item :label="t('terminationX.exitDate')">
          <el-date-picker v-model="ef.exitDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="energyVisible = false">{{ t('terminationX.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doEnergy">{{ t('terminationX.generateEnergy') }}</el-button>
      </template>
    </el-dialog>

    <!-- 结算 SettleCmd -->
    <el-dialog v-model="settleVisible" :title="t('terminationX.settleTitle')" width="520px">
      <el-alert type="info" :closable="false" show-icon
                :title="preview.formula || t('terminationX.formulaDefault')" style="margin-bottom:10px" />
      <el-form :model="st" label-width="130px">
        <el-form-item :label="t('terminationX.deposit')">
          <el-input :model-value="preview.depositAmount" disabled /></el-form-item>
        <el-form-item :label="t('terminationX.arrearsDeduction')">
          <el-input v-model.number="st.arrearsAmount" /></el-form-item>
        <el-form-item :label="t('terminationX.damageComp')">
          <el-input :model-value="preview.damageAmount" disabled /></el-form-item>
        <el-form-item :label="t('terminationX.refundTotal')">
          <el-input :model-value="totalPreview" disabled /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="settleVisible = false">{{ t('terminationX.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doSettle">{{ t('terminationX.confirmSettle') }}</el-button>
      </template>
    </el-dialog>

    <!-- 强制腾退 EnforceCmd -->
    <el-dialog v-model="enforceVisible" :title="t('terminationX.enforceTitle')" width="520px">
      <el-form :model="en" label-width="130px">
        <el-form-item :label="t('terminationX.applyDate')">
          <el-date-picker v-model="en.enforceApplyDate" type="date"
                          value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item :label="t('terminationX.court')"><el-input v-model="en.enforceCourt" /></el-form-item>
        <el-form-item :label="t('terminationX.notaryNo')"><el-input v-model="en.notaryNo" /></el-form-item>
        <el-form-item :label="t('terminationX.handler')">
          <el-input v-model="en.itemHandlerName" /></el-form-item>
        <el-form-item :label="t('terminationX.handlerPhone')">
          <el-input v-model="en.itemHandlerPhone" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="enforceVisible = false">{{ t('terminationX.cancel') }}</el-button>
        <el-button type="danger" :loading="saving" @click="doEnforce">{{ t('terminationX.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 释放 ReleaseCmd -->
    <el-dialog v-model="releaseVisible" :title="t('terminationX.releaseTitle')" width="420px">
      <el-form :model="rl" label-width="130px">
        <el-form-item :label="t('terminationX.releaseHouse')">
          <el-switch v-model="rl.houseReleased" /></el-form-item>
        <el-form-item :label="t('terminationX.revokeAccess')">
          <el-switch v-model="rl.grantRevoked" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="releaseVisible = false">{{ t('terminationX.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doRelease">{{ t('terminationX.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('alloc.detail')" width="820px" top="6vh">
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
import FilterBar from '@/components/FilterBar.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, computed, watch, onMounted } from 'vue'
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { terminationApi } from '@/api/modules'
import req from '@/api/request'
import ContractSelect from '@/components/ContractSelect.vue'
import OrgSelect from '@/components/OrgSelect.vue'
import HouseSelect from '@/components/HouseSelect.vue'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
/** 列表筛选条件（后端 /terminations 支持 status / type / contractId） */
const tf = reactive({ status: '', type: '', contractId: '', orgId: '',
  houseId: '', keyword: '' })
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const current = ref(null)

const createVisible = ref(false)
const inspectVisible = ref(false)
const settleVisible = ref(false)
const energyVisible = ref(false)
const energyPoints = ref([])
const ef = reactive({ meterPointId: '', reading: null, exitDate: '' })
const enforceVisible = ref(false)
const releaseVisible = ref(false)

const c = reactive({ contractId: null, houseId: null, personId: null,
  terminationType: 'NORMAL', planExitDate: '', exitReason: '',
  transitionMonths: 3, transitionRentMultiplier: 1.5, relocationMonths: null })
const ins = reactive({ inspectStatus: 'PASS', inspectResult: '',
  damageAmount: null, inspectImages: '' })
const st = reactive({ depositRefund: null, arrearsAmount: null })
const auto = reactive({ contractNo: '', houseName: '', orgName: '', leaseStart: '',
  leaseEnd: '', monthlyRent: '', depositAmount: '' })
const preview = reactive({ depositAmount: 0, arrearsAmount: 0, damageAmount: 0,
  totalAmount: 0, formula: '' })
const totalPreview = computed(() => {
  const dep = Number(preview.depositAmount || 0)
  const arr = Number(st.arrearsAmount || 0)
  const dmg = Number(preview.damageAmount || 0)
  return (dep - arr - dmg).toFixed(2)
})
const en = reactive({ enforceApplyDate: '', enforceCourt: '', notaryNo: '',
  itemHandlerName: '', itemHandlerPhone: '' })
const rl = reactive({ houseReleased: true, grantRevoked: true })

watch(() => c.personId, async (pid) => {
  Object.assign(auto, { contractNo: '', houseName: '', orgName: '', leaseStart: '',
    leaseEnd: '', monthlyRent: '', depositAmount: '' })
  c.contractId = null
  c.houseId = null
  if (!pid) return
  try {
    const ct = await req.get('/contracts/active-by-person/' + pid)
    if (!ct) return
    c.contractId = ct.id
    c.houseId = ct.houseId
    auto.contractNo = ct.contractNo
    auto.houseName = ct.houseIdName || ct.houseId
    auto.orgName = ct.orgIdName || ct.orgId
    auto.leaseStart = ct.leaseStart
    auto.leaseEnd = ct.leaseEnd
    auto.monthlyRent = ct.monthlyRent
    auto.depositAmount = ct.depositAmount
  } catch (e) { /* 无合同保持空 */ }
})

function openCreate() {
  Object.assign(c, { contractId: null, houseId: null, personId: null,
    terminationType: 'NORMAL', planExitDate: '', exitReason: '',
    transitionMonths: 3, transitionRentMultiplier: 1.5, relocationMonths: null })
  Object.assign(auto, { contractNo: '', houseName: '', orgName: '', leaseStart: '',
    leaseEnd: '', monthlyRent: '', depositAmount: '' })
  createVisible.value = true
}

async function load() {
  loading.value = true
  try {
    const d = await terminationApi.page({
      pageNum: pageNum.value, pageSize: pageSize.value,
      status: tf.status || undefined,
      type: tf.type || undefined,
      contractId: tf.contractId || undefined,
      orgId: tf.orgId || undefined,
      houseId: tf.houseId || undefined,
      keyword: tf.keyword || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}

/** 查询：回到第 1 页再拉 */
function resetAndLoad() {
  pageNum.value = 1
  load()
}

/** 清空全部筛选条件 */
function resetQuery() {
  tf.status = ''
  tf.type = ''
  tf.contractId = ''
  tf.orgId = ''
  tf.houseId = ''
  tf.keyword = ''
  resetAndLoad()
}

async function doCreate() {
  if (!c.contractId || !c.personId) {
    ElMessage.warning(t('termination.contractPersonRequired')); return
  }
  saving.value = true
  try {
    await terminationApi.create({ ...c })
    ElMessage.success(t('termination.created'))
    createVisible.value = false; load()
  } finally { saving.value = false }
}

async function doSubmit(row) {
  await ElMessageBox.confirm(t('termination.submitConfirm'), t('termination.submitTitle'), { type: 'warning' })
  await terminationApi.submit(row.id)
  ElMessage.success(t('termination.submitted')); load()
}

async function doReject(row) {
  const { value } = await ElMessageBox.prompt(t('termination.rejectPrompt'), t('termination.rejectTitle'),
    { inputValidator: (v) => (v && v.trim() ? true : t('termination.rejectRequired')) })
  await terminationApi.reject(row.id, value)
  ElMessage.success(t('termination.rejected')); load()
}

async function doCancel(row) {
  const { value } = await ElMessageBox.prompt(t('termination.cancelPrompt'), t('termination.cancelTitle'),
    { inputPlaceholder: t('termination.required'), inputValidator: (v) => (v && v.trim() ? true : t('termination.cancelRequired')) })
  await terminationApi.cancel(row.id, value)
  ElMessage.success(t('termination.cancelled')); load()
}

async function doComplete(row) {
  const { value } = await ElMessageBox.prompt(t('termination.completePrompt'), t('termination.completeTitle'),
    { inputValue: new Date().toISOString().slice(0, 10) })
  await terminationApi.complete(row.id, value || null)
  ElMessage.success(t('termination.completed')); load()
}

async function approve(row) {
  await ElMessageBox.confirm(t('termination.approveConfirm'), t('termination.approveTitle'), { type: 'warning' })
  await terminationApi.approve(row.id, {})
  ElMessage.success(t('termination.approved')); load()
}

function openInspect(row) { current.value = row; inspectVisible.value = true }
async function doInspect() {
  saving.value = true
  try {
    await req.post(`/terminations/${current.value.id}/inspect`, { ...ins })
    ElMessage.success('查验已提交')
    inspectVisible.value = false; load()
  } finally { saving.value = false }
}

async function openEnergy(row) {
  current.value = row
  try {
    energyPoints.value = (await req.get('/fin/meter-points')) || []
  } catch (e) { energyPoints.value = [] }
  ef.meterPointId = ''
  ef.reading = null
  ef.exitDate = row.actualExitDate || row.planExitDate || new Date().toISOString().slice(0, 10)
  energyVisible.value = true
}
async function doEnergy() {
  if (!ef.meterPointId || ef.reading == null) {
    ElMessage.warning('请选择表计并录入当前读数')
    return
  }
  saving.value = true
  try {
    await req.post('/fin/utility-allocations/exit', {
      meterPointId: ef.meterPointId,
      contractId: current.value.contractId || current.value.id,
      exitDate: ef.exitDate,
      reading: ef.reading
    })
    ElMessage.success('能耗账单已生成，可继续结算')
    energyVisible.value = false
    openSettle(current.value)
  } finally { saving.value = false }
}

async function openSettle(row) {
  current.value = row
  st.depositRefund = null
  st.arrearsAmount = null
  try {
    const pv = await req.get('/terminations/' + row.id + '/settle-preview')
    Object.assign(preview, pv || {})
    st.arrearsAmount = pv?.arrearsAmount ?? 0
    st.depositRefund = pv?.depositAmount ?? 0
  } catch (e) { ElMessage.error('结算预览加载失败') }
  settleVisible.value = true
}
async function doSettle() {
  saving.value = true
  try {
    await req.post(`/terminations/${current.value.id}/settle`,
      { depositRefund: st.depositRefund, arrearsAmount: st.arrearsAmount })
    ElMessage.success('结算完成')
    settleVisible.value = false; load()
  } finally { saving.value = false }
}

function openEnforce(row) { current.value = row; enforceVisible.value = true }
async function doEnforce() {
  saving.value = true
  try {
    await req.post(`/terminations/${current.value.id}/register-enforce`, { ...en })
    ElMessage.success('强制腾退已登记')
    enforceVisible.value = false; load()
  } finally { saving.value = false }
}

function openRelease(row) { current.value = row; releaseVisible.value = true }
async function doRelease() {
  saving.value = true
  try {
    await req.post(`/terminations/${current.value.id}/mark-released`, { ...rl })
    ElMessage.success('房源与授权已释放')
    releaseVisible.value = false; load()
  } finally { saving.value = false }
}

// 待办中心「待处理退租」跳转过来时带 pending=1
if (/pending=1/.test(window.location.hash)) {
  tf.status = 'APPLYING'
}
onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
