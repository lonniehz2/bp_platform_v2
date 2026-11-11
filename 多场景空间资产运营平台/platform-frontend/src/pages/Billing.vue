<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { can, canAction } from '../permissions'
import SearchSelect from '../components/SearchSelect.vue'
import DataTable from '../components/DataTable.vue'
import EntityDetailTabs from '../components/EntityDetailTabs.vue'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const { t } = useI18n()
const router = useRouter()
const pageTitle = computed(() => route.path === '/bills' ? t('billing.billsTitle') : t('billing.paymentsTitle'))
const project = ref(null)
const bills = ref([])
const payments = ref([])
const drillRange = ref({ start: '', end: '' })
const page = ref(1)
const billQuery = ref('')
const payOpen = ref(false)
const paymentsOpen = ref(false)
const error = ref('')
const busy = ref(false)
const payForm = reactive({ billId: '', amount: '', method: 'CASH' })
const receipt = ref(null)
const detailBill = ref(null)
const adjusting = ref(null)
const adjustForm = reactive({ discountAmount: 0, remark: '' })
const refunding = ref(null)
const refundAllocations = ref([])
const refundForm = reactive({ allocationId: '', amount: 0, reason: '' })

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
const filteredBills = computed(() => {
  const q = billQuery.value.trim().toLowerCase()
  const contractId = String(route.query.contractId || '')
  let rows = bills.value
  if (contractId) rows = rows.filter(b => String(b.contractId) === contractId)
  if (!q) return rows
  return rows.filter(b => (String(b.billNo) + ' ' + String(b.personName || '')).toLowerCase().includes(q))
})
const pagedBills = computed(() => filteredBills.value.slice((page.value - 1) * 10, page.value * 10))
const billColumns = [
  { key: 'billNo', title: t('billing.billNo'), width: '170px' },
  { key: 'personName', title: t('billing.tenant'), width: '120px' },
  { key: 'period', title: t('billing.period'), width: '200px' },
  { key: 'amount', title: t('billing.amount'), width: '100px' },
  { key: 'discountAmount', title: t('billing.discount'), width: '90px' },
  { key: 'payableAmount', title: t('billing.payable'), width: '100px' },
  { key: 'paidAmount', title: t('billing.paid'), width: '100px' },
  { key: 'billStatus', title: t('billing.status'), width: '90px' },
  { key: 'actions', title: t('billing.action'), width: '80px' }
]
const statusClass = (s) => ({ PAID: 'green', PARTIAL: 'orange', UNPAID: 'red' }[s] || '')

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  if (chosen) return chosen
  const demo = all.find(p => p.orgCode === 'DEMO_PROJECT')
  if (demo) return demo
  return all.slice().sort((a, b) =>
    ((b.contractCount || 0) + (b.applicationCount || 0) + (b.deviceCount || 0)) -
    ((a.contractCount || 0) + (a.applicationCount || 0) + (a.deviceCount || 0))
  )[0] || null
}

async function load() {
  error.value = ''
  try {
    project.value = await currentProject()
    if (!project.value) return
    localStorage.setItem('platformProjectId', project.value.id)
    const [b, p] = await Promise.all([api.bills(project.value.id), api.payments(project.value.id)])
    drillRange.value = { start: String(route.query.periodStart || ''), end: String(route.query.periodEnd || '') }
    bills.value = b.filter(x => {
      const d = String(x.periodStart || '').slice(0, 10)
      return (!drillRange.value.start || d >= drillRange.value.start)
        && (!drillRange.value.end || d <= drillRange.value.end)
    })
    payments.value = p
    if (!payForm.billId && b.length) selectBill(b[0])
  } catch (e) { error.value = e.message }
}

function selectBill(b) {
  payForm.billId = b.id
  payForm.amount = Number(b.payableAmount || b.amount) - Number(b.paidAmount || 0)
}

function openAdjust(b) { adjusting.value = b; adjustForm.discountAmount = 0; adjustForm.remark = '' }

async function adjust() {
  busy.value = true; error.value = ''
  try {
    if (!adjusting.value) return
    await api.adjustBill(adjusting.value.id, { discountAmount: Number(adjustForm.discountAmount || 0), remark: adjustForm.remark })
    adjusting.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function openRefund(p) {
  error.value = ''
  try {
    refunding.value = p
    refundAllocations.value = await api.paymentAllocations(p.id)
    const first = refundAllocations.value[0]
    refundForm.allocationId = first ? first.allocationId : ''
    refundForm.amount = first ? Number(first.amount) - Number(first.refunded || 0) : 0
    refundForm.reason = ''
  } catch (e) { error.value = e.message }
}

function pickAllocation() {
  const a = refundAllocations.value.find(x => String(x.allocationId) === String(refundForm.allocationId))
  refundForm.amount = a ? Number(a.amount) - Number(a.refunded || 0) : 0
}

async function submitRefund() {
  busy.value = true; error.value = ''
  try {
    if (!refunding.value || !refundForm.allocationId) throw new Error(t('billing.requiredAllocation'))
    await api.refundPayment(refunding.value.id, {
      billId: refundAllocations.value.find(x => String(x.allocationId) === String(refundForm.allocationId))?.billId,
      amount: Number(refundForm.amount),
      reason: refundForm.reason
    })
    refunding.value = null
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}


async function discardBill(b) {
  if (!window.confirm(t('billing.confirmDiscard', { no: b.billNo }))) return
  busy.value = true; error.value = ''
  try { await api.discardBill(b.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function closeBill(b) {
  if (!window.confirm(t('billing.confirmClose', { no: b.billNo }))) return
  busy.value = true; error.value = ''
  try { await api.closeBill(b.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

function openReceipt(p) { receipt.value = p }
function printReceipt() { window.print() }

async function pay() {
  busy.value = true; error.value = ''
  try {
    if (!payForm.billId) throw new Error(t('billing.requiredBill'))
    await api.pay(payForm.billId, { amount: Number(payForm.amount), paymentMethod: payForm.method })
    payForm.billId = ''
    payForm.amount = ''
    payOpen.value = false
    await load()
  } catch (e) { error.value = e.message } finally { busy.value = false }
}

onMounted(load)
</script>

<template>
  <div>
    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="route.query.contractId" class="alert">{{ t('billing.onlyContract', { id: route.query.contractId }) }} <button class="sm" @click="router.replace('/guarantee/billing')">{{ t('billing.clear') }}</button></div>
    <div v-if="!project" class="empty">{{ t('billing.createProject') }}</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>{{ pageTitle }}</h2><p>{{ project.orgName }} · {{ t('billing.subtitle') }}</p></div>
          <div class="row"><button v-if="canAction('billing:pay', 'billing')" class="primary" @click="payOpen = true">{{ t('billing.pay') }}</button><button class="sm" @click="paymentsOpen = !paymentsOpen">{{ paymentsOpen ? t('billing.hidePayments') : t('billing.payments') }}</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>{{ t('billing.list') }}</h2><span class="small muted" v-if="drillRange.start">{{ t('billing.periodRange', { start: drillRange.start, end: drillRange.end }) }} · {{ t('billing.receivable', { n: bills.length }) }}</span><span class="small muted" v-else>{{ t('billing.receivable', { n: bills.length }) }}</span></div>
        <div class="row" style="margin-bottom:8px">
          <input v-model="billQuery" :placeholder="t('billing.search')" style="max-width:260px" @input="page = 1" />
        </div>
        <DataTable :rows="pagedBills" :columns="billColumns" :page="page" :page-size="10" :total="filteredBills.length" :empty-text="t('billing.noBills')" @update:page="page = $event">
          <template #cell-period="{ row }"><span class="small">{{ row.periodStart }} ~ {{ row.periodEnd }}</span></template>
          <template #cell-amount="{ row }">¥{{ money(row.amount) }}</template>
          <template #cell-discountAmount="{ row }">¥{{ money(row.discountAmount) }}</template>
          <template #cell-payableAmount="{ row }">¥{{ money(row.payableAmount || row.amount) }}</template>
          <template #cell-paidAmount="{ row }">¥{{ money(row.paidAmount) }}</template>
          <template #cell-billStatus="{ row }"><span class="badge" :class="statusClass(row.billStatus)">{{ row.billStatus }}</span></template>
          <template #cell-actions="{ row }">
            <button v-if="canAction('billing:adjust', 'billing') && row.billStatus !== 'PAID'" class="sm" :disabled="busy" @click="openAdjust(row)">{{ t('billing.adjust') }}</button>
            <button v-if="canAction('billing:discard', 'billing') && row.billStatus === 'DRAFT'" class="sm danger" @click="discardBill(row)">{{ t('billing.discard') }}</button>
            <button v-if="canAction('billing:close', 'billing') && row.billStatus === 'WAIVED'" class="sm" @click="closeBill(row)">{{ t('billing.close') }}</button>
            <RouterLink class="sm" :to="`/guarantee/detail/BILL/${row.id}`">{{ t('billing.detail') }}</RouterLink>
          </template>
        </DataTable>
      </div>

      <div v-if="paymentsOpen" class="panel">
        <div class="panel-head"><h2>{{ t('billing.payments') }}</h2><span class="small muted">{{ t('billing.paymentHint') }}</span></div>
        <div v-if="!payments.length" class="empty">{{ t('billing.noPayments') }}</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>{{ t('billing.paymentNo') }}</th><th>{{ t('billing.amount') }}</th><th>{{ t('billing.method') }}</th><th>{{ t('billing.status') }}</th><th>{{ t('billing.receipt') }}</th><th>{{ t('billing.time') }}</th><th>{{ t('billing.action') }}</th></tr></thead>
            <tbody>
              <tr v-for="p in payments" :key="p.id">
                <td class="mono">{{ p.paymentNo }}</td><td>¥{{ money(p.amount) }}</td><td>{{ p.paymentMethod }}</td>
                <td><span class="badge green">{{ p.paymentStatus }}</span></td><td class="mono">{{ p.receiptNo || '-' }}</td><td class="small">{{ p.paidTime }}</td>
                <td><div class="row"><button v-if="p.receiptNo" class="sm" :disabled="busy" @click="openReceipt(p)">{{ t('billing.print') }}</button><button v-if="canAction('billing:refund', 'billing')" class="sm" @click="openRefund(p)">{{ t('billing.refund') }}</button></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-if="payOpen" class="modal-mask" @click.self="payOpen = false">
      <div class="modal" style="max-width:640px">
        <div class="panel-head"><h2>{{ t('billing.payTitle') }}</h2><button class="sm" @click="payOpen = false">{{ t('billing.close') }}</button></div>
        <div class="row">
          <div class="field"><label>{{ t('billing.bill') }}</label><SearchSelect v-model="payForm.billId" :options="bills.filter(x => x.billStatus !== 'PAID')" label-key="billNo" sublabel-key="personName" value-key="id" :placeholder="t('billing.search')" @change="selectBill" /></div>
          <div class="field"><label>{{ t('billing.payAmount') }}</label><input v-model.number="payForm.amount" type="number" /></div>
          <div class="field"><label>{{ t('billing.method') }}</label><select v-model="payForm.method"><option value="CASH">{{ t('billing.cash') }}</option><option value="WECHAT">{{ t('billing.wechat') }}</option><option value="ALIPAY">{{ t('billing.alipay') }}</option><option value="BANK">{{ t('billing.bank') }}</option></select></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="pay">{{ t('billing.confirmPay') }}</button></div>
      </div>
    </div>

    <div v-if="refunding" class="modal-mask" @click.self="refunding = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('billing.refundTitle') }}</h2><button class="sm" @click="refunding = null">{{ t('billing.close') }}</button></div>
        <div class="field"><label>{{ t('billing.original') }}</label><div class="mono">{{ refunding.paymentNo }} · ¥{{ money(refunding.amount) }}</div></div>
        <div class="field"><label>{{ t('billing.allocation') }}</label>
          <select v-model="refundForm.allocationId" @change="pickAllocation">
            <option v-for="a in refundAllocations" :key="a.allocationId" :value="a.allocationId">
              {{ a.billNo }} · {{ a.periodStart }} ~ {{ a.periodEnd }} · {{ t('billing.refundable') }} ¥{{ money(Number(a.amount) - Number(a.refunded || 0)) }}
            </option>
          </select>
        </div>
        <div class="field"><label>{{ t('billing.refundAmount') }}</label><input v-model.number="refundForm.amount" type="number" /></div>
        <div class="field"><label>{{ t('billing.refundReason') }}</label><input v-model="refundForm.reason" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="submitRefund">{{ t('billing.confirmRefund') }}</button></div>
      </div>
    </div>

    <div v-if="adjusting" class="modal-mask" @click.self="adjusting = null">
      <div class="modal">
        <div class="panel-head"><h2>{{ t('billing.adjustTitle') }}</h2><button class="sm" @click="adjusting = null">{{ t('billing.close') }}</button></div>
        <div class="field"><label>{{ t('billing.bill') }}</label><div class="mono">{{ adjusting.billNo }}</div></div>
        <div class="field"><label>{{ t('billing.newDiscount') }}</label><input v-model.number="adjustForm.discountAmount" type="number" /></div>
        <div class="field"><label>{{ t('billing.adjustReason') }}</label><input v-model="adjustForm.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="adjust">{{ t('billing.save') }}</button></div>
      </div>
    </div>

    <div v-if="detailBill" class="modal-mask" @click.self="detailBill = null">
      <div class="modal" style="max-width:760px">
        <div class="panel-head"><div><h2>{{ detailBill.billNo }}</h2><p class="small muted">{{ t('billing.billRelations') }}</p></div><button class="sm" @click="detailBill = null">{{ t('billing.close') }}</button></div>
        <EntityDetailTabs type="BILL" :entity-id="detailBill.id" />
      </div>
    </div>

    <div v-if="receipt" class="modal-mask" @click.self="receipt = null">
      <div class="modal receipt-box">
        <div class="panel-head"><h2>{{ t('billing.receiptTitle') }}</h2><button class="sm no-print" @click="receipt = null">{{ t('billing.close') }}</button></div>
        <div class="receipt">
          <h3>{{ t('billing.receiptTitle') }}</h3>
          <p>{{ t('billing.receiptNo') }}: {{ receipt.receiptNo }}</p>
          <p>{{ t('billing.paymentNo') }}: {{ receipt.paymentNo }}</p>
          <p>{{ t('billing.payAmount') }}: ¥{{ money(receipt.amount) }}</p>
          <p>{{ t('billing.method') }}: {{ receipt.paymentMethod }}</p>
          <p>{{ t('billing.time') }}: {{ receipt.paidTime }}</p>
          <p class="small muted">{{ t('billing.receiptFooter') }}</p>
        </div>
        <div class="row no-print" style="justify-content:flex-end;margin-top:12px">
          <button class="primary" @click="printReceipt">{{ t('billing.print') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
