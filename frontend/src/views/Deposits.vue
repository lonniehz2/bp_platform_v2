<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">{{ t('deposit.title') }}</h3>
        <el-tag size="small" type="info">
          {{ t('deposit.formula') }}
        </el-tag>
        <div class="spacer" />
        <el-button type="success" @click="depVisible = true">{{ t('deposit.create') }}</el-button>
      </div>

      <FilterBar @search="load" @reset="resetQuery">
      <ContractSelect v-model="df.contractId" width="200px" testid="contract-select" />
      <PersonPicker v-model="df.personId" width="240px" testid="person-picker" />
    </FilterBar>

    <el-table :data="rows" v-loading="loading" border size="small" empty-text="暂无数据，可调整筛选条件或点击右上角新建">
        <el-table-column prop="contractId" :label="t('deposit.contract')" width="130">
          <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
        </el-table-column>
        <el-table-column prop="personId" :label="t('deposit.person')" width="110">
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column :label="t('deposit.receivable')" width="100" >
          <template #default="{ row }">{{ $money(row.depositAmount) }}</template>
        </el-table-column>
        <el-table-column :label="t('deposit.received')" width="100" >
          <template #default="{ row }">{{ $money(row.paidAmount) }}</template>
        </el-table-column>
        <el-table-column :label="t('deposit.deducted')" width="100" >
          <template #default="{ row }">{{ $money(row.deductAmount) }}</template>
        </el-table-column>
        <el-table-column :label="t('deposit.refunded')" width="100" >
          <template #default="{ row }">{{ $money(row.refundAmount) }}</template>
        </el-table-column>
        <el-table-column :label="t('deposit.balance')" width="100" >
          <template #default="{ row }">{{ $money(row.balanceAmount) }}</template>
        </el-table-column>
        <el-table-column prop="depositStatus" :label="t('deposit.status')" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.depositStatus === 'REFUNDED' ? 'success'
              : (row.depositStatus === 'DEDUCTED' ? 'warning' : 'info')">
              {{ row.depositStatusLabel || enumLabel('depositStatus', row.depositStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('deposit.actions')" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('deposit.detail') }}</el-button>
            <el-button link type="primary" @click="openAmount(row, 'receive')">{{ t('deposit.receive') }}</el-button>
            <el-button link type="warning" @click="openAmount(row, 'deduct')">{{ t('deposit.deduct') }}</el-button>
            <el-button link type="success" @click="openRefund(row)">{{ t('deposit.refund') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                     :total="+depositTotal || 0" :page-size="depositSize"
                     :current-page="depositPage" :page-sizes="[10, 20, 50, 100]"
                     @current-change="(p) => { depositPage = p; load() }"
                     @size-change="(sz) => { depositSize = sz; depositPage = 1; load() }" />
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">{{ t('misc.refundList') }}</h4>
      <el-table :data="refunds" border size="small">
        <el-table-column prop="refundNo" :label="t('deposit.refundNo')" width="170" />
        <el-table-column prop="contractId" label="合同" width="130">
          <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
        </el-table-column>
        <el-table-column :label="t('deposit.amount')" width="110" >
          <template #default="{ row }">{{ $money(row.refundAmount) }}</template>
        </el-table-column>
        <el-table-column prop="refundType" :label="t('deposit.type')" width="110">
          <template #default="{ row }">{{ row.refundTypeLabel || enumLabel('refundType', row.refundType) }}</template>
        </el-table-column>
        <el-table-column prop="refundStatus" :label="t('deposit.statusCol')" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.refundStatus === 'SUCCESS' ? 'success'
              : (row.refundStatus === 'REJECTED' ? 'danger' : 'warning')">
              {{ row.refundStatusLabel || enumLabel('refundStatus', row.refundStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('deposit.actions')" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.refundStatus !== 'PENDING'"
                       @click="approve(row)">{{ t('misc.approve') }}</el-button>
            <el-button link type="danger" :disabled="row.refundStatus !== 'PENDING'"
                       @click="reject(row)">{{ t('deposit.reject') }}</el-button>
            <el-button link type="success" :disabled="row.refundStatus !== 'APPROVED'"
                       @click="complete(row)">{{ t('misc.payComplete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 押金建档 DepositCreateCmd -->
    <el-dialog v-model="depVisible" :title="t('deposit.createTitle')" width="500px">
      <el-form :model="dp" label-width="120px">
        <el-form-item :label="t('deposit.contractId')"><el-input v-model="dp.contractId"
                     @blur="fillFromContract" />
        </el-form-item>
        <el-form-item :label="t('deposit.personId')">
          <PersonPicker v-model="dp.personId" width="240px"
                        testid="person-picker" @update:model-value="fillFromPerson" />
          <span v-if="dp.personId" class="muted" style="margin-left:8px;font-size:12px">
            已带出人员ID：{{ dp.personId }}
          </span>
        </el-form-item>
        <el-form-item :label="t('deposit.depositAmount')"><el-input v-model.number="dp.depositAmount" />
        </el-form-item>
        <el-form-item :label="t('deposit.paidAmount')"><el-input v-model.number="dp.paidAmount" />
        </el-form-item>
        <el-form-item :label="t('deposit.cap')"><el-input v-model.number="dp.capAmount" />
          <span class="muted">{{ t('misc.capHint') }}</span>
        </el-form-item>
        <el-form-item :label="t('deposit.exempt')">
          <el-switch v-model="dp.isExempt" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item v-if="dp.isExempt === 1" :label="t('deposit.exemptReason')">
          <el-input v-model="dp.exemptReason" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="depVisible = false">{{ t('deposit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doDeposit">{{ t('deposit.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 收取/抵扣 AmountCmd -->
    <el-dialog v-model="amtVisible" :title="amtMode === 'receive' ? t('deposit.receiveTitle') : t('deposit.deductTitle')"
               width="440px">
      <el-form :model="am" label-width="110px">
        <el-form-item label="合同">
          <el-input :model-value="current?.contractId" disabled /></el-form-item>
        <el-form-item :label="t('deposit.currentBalance')">
          <el-input :model-value="current?.balanceAmount" disabled /></el-form-item>
        <el-form-item :label="t('deposit.amount')"><el-input v-model.number="am.amount" /></el-form-item>
        <el-form-item v-if="amtMode === 'deduct'" :label="t('deposit.reason')">
          <el-input v-model="am.reason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="amtVisible = false">{{ t('deposit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doAmount">{{ t('deposit.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 退款申请 RefundCreateCmd -->
    <el-dialog v-model="refVisible" :title="t('deposit.refundTitle')" width="480px">
      <el-form :model="rf" label-width="110px">
        <el-form-item label="合同">
          <el-input :model-value="current?.contractId" disabled /></el-form-item>
        <el-form-item :label="t('deposit.available')">
          <el-input :model-value="current?.balanceAmount" disabled /></el-form-item>
        <el-form-item :label="t('deposit.refundAmount')">
          <el-input v-model.number="rf.refundAmount" :placeholder="t('deposit.refundAmount')" />
        </el-form-item>
        <el-form-item :label="t('deposit.refundType')">
          <el-select v-model="rf.refundType" style="width:100%">
            <el-option :label="t('deposit.depositRefund')" value="DEPOSIT" />
            <el-option :label="t('deposit.overpay')" value="OVERPAY" />
          </el-select></el-form-item>
        <el-form-item :label="t('deposit.channel')">
          <el-select v-model="rf.refundChannel" style="width:100%">
            <el-option :label="t('deposit.original')" value="ORIGINAL" />
            <el-option :label="t('deposit.bank')" value="BANK" />
            <el-option :label="t('deposit.cash')" value="CASH" />
          </el-select></el-form-item>
        <el-form-item :label="t('deposit.refundReason')">
          <el-input v-model="rf.refundReason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <el-alert type="warning" :closable="false" show-icon
                :title="t('misc.refundTip')" />
      <template #footer>
        <el-button @click="refVisible = false">{{ t('deposit.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doRefund">{{ t('deposit.submit') }}</el-button>
      </template>
    </el-dialog>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
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
import { ref, reactive, watch, onMounted } from 'vue'
import DetailView from '@/components/DetailView.vue'
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/modules'
import req from '@/api/request'
import ContractSelect from '@/components/ContractSelect.vue'
import FilterBar from '@/components/FilterBar.vue'

const loading = ref(false)
const depositPage = ref(1)
const depositSize = ref(20)
const depositTotal = ref(0)
const saving = ref(false)
const rows = ref([])
const refunds = ref([])
const current = ref(null)

const depVisible = ref(false)
const dp = reactive({ contractId: null, personId: null, depositAmount: null,
  paidAmount: 0, capAmount: 1000, isExempt: 0, exemptReason: '' })

/** 选人员：带出其生效合同与应收押金 */
async function fillFromPerson(pid) {
  if (!pid) return
  try {
    const c = await req.get('/contracts/active-by-person/' + pid)
    if (c) {
      dp.contractId = c.id
      if (c.depositAmount != null) dp.depositAmount = c.depositAmount
      ElMessage.success('已带出合同 ' + (c.contractNo || c.id) + ' 与应收押金')
    } else {
      ElMessage.warning('该人员没有生效中的合同')
    }
  } catch (e) {
    ElMessage.warning('未找到该人员的合同')
  }
}

async function fillFromContract() {
  const cid = String(dp.contractId || '').trim()
  if (!cid) return
  if (!/^\d+$/.test(cid)) {
    ElMessage.warning('合同ID为数字（可在合同列表复制）；也可改选人员，系统会自动带出合同')
    return
  }
  dp.contractId = cid
  try {
    const c = await req.get('/contracts/' + dp.contractId)
    if (c) {
      dp.personId = c.lesseePersonId
      if (c.depositAmount != null) dp.depositAmount = c.depositAmount
    }
  } catch (e) {
    ElMessage.warning('未找到该合同，请检查合同ID')
  }
}

const amtVisible = ref(false)
const amtMode = ref('receive')
const am = reactive({ amount: null, reason: '' })

const refVisible = ref(false)
const rf = reactive({ refundAmount: null, refundType: 'DEPOSIT',
  refundChannel: 'ORIGINAL', refundReason: '' })

/** 筛选条件（后端 /fin/deposits、/fin/refunds 均支持 contractId/personId） */
const df = reactive({ contractId: '', personId: '' })

async function load() {
  loading.value = true
  try {
    const params = {
      pageNum: depositPage.value, pageSize: depositSize.value,
      contractId: df.contractId || undefined,
      personId: df.personId || undefined
    }
    const d = await financeApi.deposits(params)
    rows.value = d.rows || []
    depositTotal.value = Number(d.total || rows.value.length)
    const r = await req.get('/fin/refunds', { params })
    refunds.value = r.rows || r || []
  } catch (e) { /* 拦截器已提示 */ } finally { loading.value = false }
}

/** 清空筛选 */
function resetQuery() {
  df.contractId = ''
  df.personId = ''
  load()
}

async function doDeposit() {
  if (!dp.contractId || !dp.depositAmount) {
    ElMessage.warning('合同与应收押金必填'); return
  }
  saving.value = true
  try {
    await req.post('/fin/deposits', { ...dp })
    ElMessage.success('押金台账已建立')
    depVisible.value = false; load()
  } finally { saving.value = false }
}

function openAmount(row, mode) {
  current.value = row; amtMode.value = mode; am.amount = null; am.reason = ''
  amtVisible.value = true
}
async function doAmount() {
  if (!am.amount || am.amount <= 0) { ElMessage.warning('金额必须大于 0'); return }
  saving.value = true
  try {
    const url = `/fin/deposits/${current.value.id}/` +
      (amtMode.value === 'receive' ? 'receive' : 'deduct')
    await req.post(url, { amount: am.amount, reason: am.reason })
    ElMessage.success('操作成功')
    amtVisible.value = false; load()
  } finally { saving.value = false }
}

function openRefund(row) {
  current.value = row
  rf.refundAmount = null; rf.refundReason = ''
  refVisible.value = true
}
async function doRefund() {
  if (!rf.refundAmount || rf.refundAmount <= 0) {
    ElMessage.warning('退款金额必填且大于 0'); return
  }
  saving.value = true
  try {
    await req.post('/fin/refunds', {
      contractId: current.value.contractId,
      personId: current.value.personId,
      refundAmount: rf.refundAmount, refundType: rf.refundType,
      refundChannel: rf.refundChannel, refundReason: rf.refundReason
    })
    ElMessage.success('退款申请已提交')
    refVisible.value = false; load()
  } finally { saving.value = false }
}

async function approve(row) {
  await req.post(`/fin/refunds/${row.id}/approve`, { approveById: 1001 })
  ElMessage.success('已批准'); load()
}
async function reject(row) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因', '驳回退款')
  await req.post(`/fin/refunds/${row.id}/reject`, { approveById: 1001, reason: value })
  ElMessage.success('已驳回'); load()
}
async function complete(row) {
  await req.post(`/fin/refunds/${row.id}/complete`)
  ElMessage.success('打款完成，押金余额已同步扣减'); load()
}

onMounted(load)
</script>
