<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { can, canAction } from '../permissions'
import SearchSelect from '../components/SearchSelect.vue'
import DataTable from '../components/DataTable.vue'

const route = useRoute()
const pageTitle = route.path === '/bills' ? '账单与缴费' : '收款'
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
const adjusting = ref(null)
const adjustForm = reactive({ discountAmount: 0, remark: '' })
const refunding = ref(null)
const refundAllocations = ref([])
const refundForm = reactive({ allocationId: '', amount: 0, reason: '' })

const money = (v) => Number(v || 0).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
const filteredBills = computed(() => {
  const q = billQuery.value.trim().toLowerCase()
  if (!q) return bills.value
  return bills.value.filter(b => (String(b.billNo) + ' ' + String(b.personName || '')).toLowerCase().includes(q))
})
const pagedBills = computed(() => filteredBills.value.slice((page.value - 1) * 10, page.value * 10))
const billColumns = [
  { key: 'billNo', title: '账单号', width: '170px' },
  { key: 'personName', title: '承租人', width: '120px' },
  { key: 'period', title: '周期', width: '200px' },
  { key: 'amount', title: '账单金额', width: '100px' },
  { key: 'discountAmount', title: '补贴', width: '90px' },
  { key: 'payableAmount', title: '应付', width: '100px' },
  { key: 'paidAmount', title: '已收', width: '100px' },
  { key: 'billStatus', title: '状态', width: '90px' },
  { key: 'actions', title: '操作', width: '80px' }
]
const statusClass = (s) => ({ PAID: 'green', PARTIAL: 'orange', UNPAID: 'red' }[s] || '')

async function currentProject() {
  const all = await api.projects()
  const saved = String(localStorage.getItem('platformProjectId') || '')
  const chosen = all.find(p => String(p.id) === saved)
  if (chosen) return chosen
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
    if (!refunding.value || !refundForm.allocationId) throw new Error('请选择原收款分配')
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
  if (!window.confirm(`确认作废账单 ${b.billNo}？`)) return
  busy.value = true; error.value = ''
  try { await api.discardBill(b.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

async function closeBill(b) {
  if (!window.confirm(`确认关闭账单 ${b.billNo}？`)) return
  busy.value = true; error.value = ''
  try { await api.closeBill(b.id); await load() } catch (e) { error.value = e.message } finally { busy.value = false }
}

function openReceipt(p) { receipt.value = p }
function printReceipt() { window.print() }

async function pay() {
  busy.value = true; error.value = ''
  try {
    if (!payForm.billId) throw new Error('请选择账单')
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
    <div v-if="!project" class="empty">请先创建项目</div>
    <template v-else>
      <div class="panel">
        <div class="panel-head"><div><h2>{{ pageTitle }}</h2><p>{{ project.orgName }} · 账单列表与收款</p></div>
          <div class="row"><button v-if="canAction('billing:pay', 'billing')" class="primary" @click="payOpen = true">收款</button><button class="sm" @click="paymentsOpen = !paymentsOpen">{{ paymentsOpen ? '隐藏收款记录' : '收款记录' }}</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>账单列表</h2><span class="small muted" v-if="drillRange.start">账期 {{ drillRange.start }} ~ {{ drillRange.end }} · 应收 {{ bills.length }} 笔</span><span class="small muted" v-else>应收 {{ bills.length }} 笔</span></div>
        <div class="row" style="margin-bottom:8px">
          <input v-model="billQuery" placeholder="搜索账单号/承租人" style="max-width:260px" @input="page = 1" />
        </div>
        <DataTable :rows="pagedBills" :columns="billColumns" :page="page" :page-size="10" :total="filteredBills.length" empty-text="暂无账单" @update:page="page = $event">
          <template #cell-period="{ row }"><span class="small">{{ row.periodStart }} ~ {{ row.periodEnd }}</span></template>
          <template #cell-amount="{ row }">¥{{ money(row.amount) }}</template>
          <template #cell-discountAmount="{ row }">¥{{ money(row.discountAmount) }}</template>
          <template #cell-payableAmount="{ row }">¥{{ money(row.payableAmount || row.amount) }}</template>
          <template #cell-paidAmount="{ row }">¥{{ money(row.paidAmount) }}</template>
          <template #cell-billStatus="{ row }"><span class="badge" :class="statusClass(row.billStatus)">{{ row.billStatus }}</span></template>
          <template #cell-actions="{ row }">
            <button v-if="canAction('billing:adjust', 'billing') && row.billStatus !== 'PAID'" class="sm" :disabled="busy" @click="openAdjust(row)">调整</button>
            <button v-if="canAction('billing:discard', 'billing') && row.billStatus === 'DRAFT'" class="sm danger" @click="discardBill(row)">作废</button>
            <button v-if="canAction('billing:close', 'billing') && row.billStatus === 'WAIVED'" class="sm" @click="closeBill(row)">关闭</button>
          </template>
        </DataTable>
      </div>

      <div v-if="paymentsOpen" class="panel">
        <div class="panel-head"><h2>收款记录</h2><span class="small muted">收据随收款自动生成</span></div>
        <div v-if="!payments.length" class="empty">暂无收款</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>收款单号</th><th>金额</th><th>方式</th><th>状态</th><th>收据</th><th>时间</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="p in payments" :key="p.id">
                <td class="mono">{{ p.paymentNo }}</td><td>¥{{ money(p.amount) }}</td><td>{{ p.paymentMethod }}</td>
                <td><span class="badge green">{{ p.paymentStatus }}</span></td><td class="mono">{{ p.receiptNo || '-' }}</td><td class="small">{{ p.paidTime }}</td>
                <td><div class="row"><button v-if="p.receiptNo" class="sm" :disabled="busy" @click="openReceipt(p)">打印</button><button v-if="canAction('billing:refund', 'billing')" class="sm" @click="openRefund(p)">退款</button></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-if="payOpen" class="modal-mask" @click.self="payOpen = false">
      <div class="modal" style="max-width:640px">
        <div class="panel-head"><h2>收款</h2><button class="sm" @click="payOpen = false">关闭</button></div>
        <div class="row">
          <div class="field"><label>账单</label><SearchSelect v-model="payForm.billId" :options="bills.filter(x => x.billStatus !== 'PAID')" label-key="billNo" sublabel-key="personName" value-key="id" placeholder="搜索账单号/承租人" @change="selectBill" /></div>
          <div class="field"><label>收款金额</label><input v-model.number="payForm.amount" type="number" /></div>
          <div class="field"><label>方式</label><select v-model="payForm.method"><option value="CASH">现金</option><option value="WECHAT">微信</option><option value="ALIPAY">支付宝</option><option value="BANK">银行</option></select></div>
        </div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="pay">确认收款</button></div>
      </div>
    </div>

    <div v-if="refunding" class="modal-mask" @click.self="refunding = null">
      <div class="modal">
        <div class="panel-head"><h2>账单退款</h2><button class="sm" @click="refunding = null">关闭</button></div>
        <div class="field"><label>原收款</label><div class="mono">{{ refunding.paymentNo }} · ¥{{ money(refunding.amount) }}</div></div>
        <div class="field"><label>原收款分配</label>
          <select v-model="refundForm.allocationId" @change="pickAllocation">
            <option v-for="a in refundAllocations" :key="a.allocationId" :value="a.allocationId">
              {{ a.billNo }} · {{ a.periodStart }} ~ {{ a.periodEnd }} · 可退 ¥{{ money(Number(a.amount) - Number(a.refunded || 0)) }}
            </option>
          </select>
        </div>
        <div class="field"><label>退款金额</label><input v-model.number="refundForm.amount" type="number" /></div>
        <div class="field"><label>退款原因</label><input v-model="refundForm.reason" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="submitRefund">确认退款</button></div>
      </div>
    </div>

    <div v-if="adjusting" class="modal-mask" @click.self="adjusting = null">
      <div class="modal">
        <div class="panel-head"><h2>账单调整</h2><button class="sm" @click="adjusting = null">关闭</button></div>
        <div class="field"><label>账单</label><div class="mono">{{ adjusting.billNo }}</div></div>
        <div class="field"><label>新增减免</label><input v-model.number="adjustForm.discountAmount" type="number" /></div>
        <div class="field"><label>调整原因</label><input v-model="adjustForm.remark" /></div>
        <div class="row" style="justify-content:flex-end;margin-top:12px"><button class="primary" :disabled="busy" @click="adjust">保存</button></div>
      </div>
    </div>

    <div v-if="receipt" class="modal-mask" @click.self="receipt = null">
      <div class="modal receipt-box">
        <div class="panel-head"><h2>收款收据</h2><button class="sm no-print" @click="receipt = null">关闭</button></div>
        <div class="receipt">
          <h3>保障房租金收据</h3>
          <p>收据号：{{ receipt.receiptNo }}</p>
          <p>收款单号：{{ receipt.paymentNo }}</p>
          <p>收款金额：¥{{ money(receipt.amount) }}</p>
          <p>收款方式：{{ receipt.paymentMethod }}</p>
          <p>收款时间：{{ receipt.paidTime }}</p>
          <p class="small muted">本收据由多场景空间资产运营平台生成</p>
        </div>
        <div class="row no-print" style="justify-content:flex-end;margin-top:12px">
          <button class="primary" @click="printReceipt">打印</button>
        </div>
      </div>
    </div>
  </div>
</template>
