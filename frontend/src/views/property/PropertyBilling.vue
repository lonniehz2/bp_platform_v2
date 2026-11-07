<template>
  <div class="billing-page">
    <el-alert v-if="!projectId" type="warning" :closable="false" show-icon
              :title="t('propertyBilling.noProject')" />

    <el-card shadow="never">
      <div class="toolbar">
        <div>
          <div class="title">{{ t('propertyBilling.feeItems') }}</div>
          <div class="sub">{{ t('propertyBilling.feeHint') }}</div>
        </div>
        <div class="spacer" />
        <el-button type="primary" @click="openFee">{{ t('propertyBilling.addFee') }}</el-button>
      </div>
      <el-table :data="feeItems" border size="small" v-loading="loading">
        <el-table-column prop="feeItemCode" :label="t('propertyBilling.code')" width="150" />
        <el-table-column prop="feeItemName" :label="t('propertyBilling.name')" min-width="160" />
        <el-table-column prop="incomeCategory" :label="t('propertyBilling.category')" width="160" />
        <el-table-column prop="chargeBasis" :label="t('propertyBilling.basis')" width="130" />
        <el-table-column prop="billingCycle" :label="t('propertyBilling.cycle')" width="110" />
        <el-table-column prop="defaultPrice" :label="t('propertyBilling.price')" width="120" />
        <el-table-column prop="unit" :label="t('propertyBilling.unit')" width="110" />
      </el-table>
    </el-card>

    <el-card shadow="never">
      <div class="toolbar">
        <div>
          <div class="title">{{ t('propertyBilling.bills') }}</div>
          <div class="sub">{{ t('propertyBilling.billHint') }}</div>
        </div>
        <div class="spacer" />
        <el-select v-model="status" clearable :placeholder="t('propertyBilling.status')"
                   style="width:130px" @change="loadBills">
          <el-option label="PENDING" value="PENDING" />
          <el-option label="PAID" value="PAID" />
          <el-option label="OVERDUE" value="OVERDUE" />
        </el-select>
        <el-button @click="loadBills">{{ t('propertyBilling.refresh') }}</el-button>
        <el-button type="primary" @click="openGenerate">{{ t('propertyBilling.generate') }}</el-button>
        <el-button type="success" :disabled="!selected.length" @click="openPay">
          {{ t('propertyBilling.paySelected', { n: selected.length }) }}
        </el-button>
      </div>

      <el-table :data="bills" border size="small" v-loading="loading" @selection-change="(v) => (selected = v)">
        <el-table-column type="selection" width="46" :selectable="canPay" />
        <el-table-column prop="billNo" :label="t('propertyBilling.billNo')" width="190" />
        <el-table-column prop="houseName" :label="t('propertyBilling.house')" min-width="170" />
        <el-table-column prop="feeItemName" :label="t('propertyBilling.feeItem')" width="130" />
        <el-table-column :label="t('propertyBilling.period')" width="190">
          <template #default="{ row }">{{ row.periodStart }} ~ {{ row.periodEnd }}</template>
        </el-table-column>
        <el-table-column prop="payableAmount" :label="t('propertyBilling.payable')" width="110" />
        <el-table-column prop="paidAmount" :label="t('propertyBilling.paid')" width="100" />
        <el-table-column prop="billStatus" :label="t('propertyBilling.status')" width="100" />
        <el-table-column :label="t('propertyBilling.actions')" width="150" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.billStatus !== 'PAID'" link type="success" @click="payOne(row)">
              {{ t('propertyBilling.pay') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="feeVisible" :title="t('propertyBilling.addFee')" width="560px">
      <el-form :model="feeForm" label-width="110px">
        <el-form-item :label="t('propertyBilling.code')" required>
          <el-input v-model="feeForm.feeItemCode" />
        </el-form-item>
        <el-form-item :label="t('propertyBilling.name')" required>
          <el-input v-model="feeForm.feeItemName" />
        </el-form-item>
        <el-form-item :label="t('propertyBilling.category')">
          <el-select v-model="feeForm.incomeCategory" style="width:100%">
            <el-option :label="t('propertyBilling.incomeProperty')" value="PROPERTY_FEE" />
            <el-option :label="t('propertyBilling.incomeParking')" value="PARKING" />
            <el-option :label="t('propertyBilling.incomeEnergy')" value="ENERGY" />
            <el-option :label="t('propertyBilling.incomeLease')" value="LEASE" />
            <el-option :label="t('propertyBilling.incomeMulti')" value="MULTI_BUSINESS" />
            <el-option :label="t('propertyBilling.incomeOther')" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyBilling.basis')">
          <el-select v-model="feeForm.chargeBasis" style="width:100%">
            <el-option :label="t('propertyBilling.basisArea')" value="AREA" />
            <el-option :label="t('propertyBilling.basisSpace')" value="SPACE_CYCLE" />
            <el-option :label="t('propertyBilling.basisMeter')" value="METER" />
            <el-option :label="t('propertyBilling.basisManual')" value="MANUAL" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyBilling.cycle')">
          <el-select v-model="feeForm.billingCycle" clearable style="width:100%">
            <el-option :label="t('propertyBilling.cycleMonth')" value="MONTH" />
            <el-option :label="t('propertyBilling.cycleQuarter')" value="QUARTER" />
            <el-option :label="t('propertyBilling.cycleHalfYear')" value="HALF_YEAR" />
            <el-option :label="t('propertyBilling.cycleYear')" value="YEAR" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyBilling.price')">
          <el-input-number v-model="feeForm.defaultPrice" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item :label="t('propertyBilling.unit')">
          <el-input v-model="feeForm.unit" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feeVisible = false">{{ t('propertyBilling.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveFee">{{ t('propertyBilling.save') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="generateVisible" :title="t('propertyBilling.generate')" width="520px">
      <el-form :model="genForm" label-width="110px">
        <el-form-item :label="t('propertyBilling.feeItem')" required>
          <el-select v-model="genForm.feeItemId" style="width:100%">
            <el-option v-for="f in feeItems" :key="f.id" :label="f.feeItemName" :value="f.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('propertyBilling.period')" required>
          <el-date-picker v-model="genForm.period" type="monthrange" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateVisible = false">{{ t('propertyBilling.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="generate">{{ t('propertyBilling.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="payVisible" :title="t('propertyBilling.pay')" width="480px">
      <div class="pay-summary">
        <div>{{ t('propertyBilling.selectedBills') }}：{{ payBills.length }}</div>
        <div>{{ t('propertyBilling.amount') }}：<b>{{ payTotal }}</b></div>
      </div>
      <el-form label-width="100px">
        <el-form-item :label="t('propertyBilling.payChannel')">
          <el-select v-model="payChannel" style="width:100%">
            <el-option :label="t('propertyBilling.wechat')" value="WECHAT" />
            <el-option :label="t('propertyBilling.alipay')" value="ALIPAY" />
            <el-option :label="t('propertyBilling.cash')" value="CASH" />
            <el-option :label="t('propertyBilling.bank')" value="BANK_TRANSFER" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payVisible = false">{{ t('propertyBilling.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="pay">{{ t('propertyBilling.confirm') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="receiptVisible" :title="t('propertyBilling.receipt')" width="440px">
      <div v-if="receipt" class="receipt">
        <div class="receipt-title">{{ t('propertyBilling.receipt') }}</div>
        <div class="receipt-no">{{ receipt.receiptNo }}</div>
        <div class="receipt-line">{{ t('propertyBilling.payer') }}：{{ receipt.payerName }}</div>
        <div class="receipt-line">{{ t('propertyBilling.amount') }}：{{ receipt.amount }}</div>
      </div>
      <template #footer>
        <el-button @click="receiptVisible = false">{{ t('propertyBilling.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import { usePropertyStore } from '@/store/property'

const { t } = useI18n()
const store = usePropertyStore()
const projectId = computed(() => store.projectId)
const feeItems = ref([])
const bills = ref([])
const selected = ref([])
const loading = ref(false)
const saving = ref(false)
const status = ref('')
const feeVisible = ref(false)
const generateVisible = ref(false)
const payVisible = ref(false)
const receiptVisible = ref(false)
const receipt = ref(null)
const payBills = ref([])
const payChannel = ref('WECHAT')
const feeForm = reactive({
  feeItemCode: '', feeItemName: '', incomeCategory: 'PROPERTY_FEE',
  chargeBasis: 'AREA', billingCycle: 'MONTH', defaultPrice: 0, unit: t('propertyBilling.unitAreaMonth')
})
const genForm = reactive({ feeItemId: null, period: [] })
const payTotal = computed(() => payBills.value.reduce(
  (s, b) => s + Number(b.payableAmount || 0) - Number(b.paidAmount || 0), 0).toFixed(2))

onMounted(async () => {
  await store.loadProjects()
  await loadAll()
})
watch(projectId, loadAll)

async function loadAll() {
  if (!projectId.value) return
  await Promise.all([loadFeeItems(), loadBills()])
}

async function loadFeeItems() {
  loading.value = true
  try {
    feeItems.value = await req.get('/property/fee-items', { params: { projectId: projectId.value } }) || []
  } catch (e) {
    ElMessage.error(t('propertyBilling.loadFailed'))
  } finally { loading.value = false }
}

async function loadBills() {
  if (!projectId.value) return
  try {
    const d = await req.get('/property/bills', {
      params: { projectId: projectId.value, pageNum: 1, pageSize: 200,
        status: status.value || undefined }
    })
    bills.value = d.rows || []
  } catch (e) {
    ElMessage.error(t('propertyBilling.loadFailed'))
  }
}

function openFee() {
  Object.assign(feeForm, {
    feeItemCode: '', feeItemName: '', incomeCategory: 'PROPERTY_FEE',
    chargeBasis: 'AREA', billingCycle: 'MONTH', defaultPrice: 0, unit: t('propertyBilling.unitAreaMonth')
  })
  feeVisible.value = true
}

async function saveFee() {
  if (!feeForm.feeItemCode.trim() || !feeForm.feeItemName.trim()) {
    ElMessage.warning(t('propertyBilling.required'))
    return
  }
  saving.value = true
  try {
    await req.post('/property/fee-items', feeForm, { params: { projectId: projectId.value } })
    ElMessage.success(t('propertyBilling.saved'))
    feeVisible.value = false
    await loadFeeItems()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyBilling.saveFailed'))
  } finally { saving.value = false }
}

function openGenerate() {
  genForm.feeItemId = feeItems.value[0]?.id || null
  const now = new Date()
  const start = new Date(now.getFullYear(), now.getMonth(), 1)
  const end = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  const f = (d) => d.toISOString().slice(0, 10)
  genForm.period = [f(start), f(end)]
  generateVisible.value = true
}

async function generate() {
  if (!genForm.feeItemId || !genForm.period?.length) {
    ElMessage.warning(t('propertyBilling.required'))
    return
  }
  saving.value = true
  try {
    const r = await req.post('/property/bills/generate', {
      projectId: projectId.value, feeItemId: genForm.feeItemId,
      periodStart: genForm.period[0], periodEnd: genForm.period[1]
    })
    ElMessage.success(t('propertyBilling.generateDone', { created: r.created, skipped: r.skipped }))
    generateVisible.value = false
    await loadBills()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyBilling.generateFailed'))
  } finally { saving.value = false }
}

function canPay(row) {
  return row.billStatus !== 'PAID' && row.billStatus !== 'CANCELLED'
}

function openPay() {
  payBills.value = selected.value
  payVisible.value = true
}

function payOne(row) {
  payBills.value = [row]
  payVisible.value = true
}

async function pay() {
  saving.value = true
  try {
    const r = await req.post('/property/payments', {
      projectId: projectId.value,
      billIds: payBills.value.map((b) => b.id),
      payAmount: Number(payTotal.value),
      payChannel: payChannel.value
    })
    ElMessage.success(t('propertyBilling.payDone'))
    payVisible.value = false
    receipt.value = { receiptNo: r.receiptNo, payerName: payBills.value[0]?.payerName, amount: r.amount }
    receiptVisible.value = true
    await loadBills()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || t('propertyBilling.payFailed'))
  } finally { saving.value = false }
}
</script>

<style scoped>
.billing-page { display: flex; flex-direction: column; gap: 12px; }
.toolbar { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; }
.title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.sub { font-size: 12px; color: #8492a6; margin-top: 3px; }
.spacer { flex: 1; }
.pay-summary { background: #f5f8ff; border-radius: 6px; padding: 10px 12px; margin-bottom: 12px; line-height: 1.9; }
.receipt { text-align: center; padding: 10px; border: 1px dashed #cbd5e1; }
.receipt-title { font-size: 18px; font-weight: 600; margin-bottom: 14px; }
.receipt-no { color: #64748b; margin-bottom: 12px; }
.receipt-line { line-height: 2; text-align: left; }
</style>
