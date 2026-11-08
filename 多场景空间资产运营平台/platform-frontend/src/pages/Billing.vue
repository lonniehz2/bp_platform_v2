<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { can } from '../permissions'
import Pager from '../components/Pager.vue'

const route = useRoute()
const pageTitle = route.path === '/bills' ? '账单与缴费' : '收款'
const project = ref(null)
const bills = ref([])
const payments = ref([])
const drillRange = ref({ start: '', end: '' })
const page = ref(1)
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
const pagedBills = computed(() => bills.value.slice((page.value - 1) * 10, page.value * 10))
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

function openReceipt(p) { receipt.value = p }
function printReceipt() { window.print() }

async function pay() {
  busy.value = true; error.value = ''
  try {
    if (!payForm.billId) throw new Error('请选择账单')
    await api.pay(payForm.billId, { amount: Number(payForm.amount), paymentMethod: payForm.method })
    payForm.billId = ''
    payForm.amount = ''
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
        <div class="panel-head"><div><h2>{{ pageTitle }}</h2><p>{{ project.orgName }} · 按应付金额收款，自动生成收据</p></div><span class="pill">BILLING</span></div>
        <div class="row">
          <div class="field"><label>账单</label>
            <select v-model="payForm.billId" @change="selectBill(bills.find(b => b.id === payForm.billId))">
              <option value="">请选择</option>
              <option v-for="b in bills.filter(x => x.billStatus !== 'PAID')" :key="b.id" :value="b.id">{{ b.billNo }} · {{ b.personName }} · ¥{{ money(b.payableAmount || b.amount) }}</option>
            </select>
          </div>
          <div class="field"><label>收款金额</label><input v-model.number="payForm.amount" type="number" /></div>
          <div class="field"><label>方式</label>
            <select v-model="payForm.method"><option value="CASH">现金</option><option value="WECHAT">微信</option><option value="ALIPAY">支付宝</option><option value="BANK">银行</option></select>
          </div>
          <div class="field" style="flex:0 0 auto"><label>&nbsp;</label><button v-if="can('billing')" class="primary" :disabled="busy" @click="pay">确认收款</button></div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head"><h2>账单列表</h2><span class="small muted" v-if="drillRange.start">账期 {{ drillRange.start }} ~ {{ drillRange.end }} · 应收 {{ bills.length }} 笔</span><span class="small muted" v-else>应收 {{ bills.length }} 笔</span></div>
        <div v-if="!bills.length" class="empty">暂无账单</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>账单号</th><th>承租人</th><th>周期</th><th>账单金额</th><th>补贴</th><th>应付</th><th>已收</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="b in pagedBills" :key="b.id">
                <td class="mono">{{ b.billNo }}</td><td>{{ b.personName }}</td>
                <td class="small">{{ b.periodStart }} ~ {{ b.periodEnd }}</td>
                <td>¥{{ money(b.amount) }}</td><td>¥{{ money(b.discountAmount) }}</td>
                <td>¥{{ money(b.payableAmount || b.amount) }}</td><td>¥{{ money(b.paidAmount) }}</td>
                <td><span class="badge" :class="statusClass(b.billStatus)">{{ b.billStatus }}</span></td>
                <td><button v-if="can('billing') && b.billStatus !== 'PAID'" class="sm" @click="openAdjust(b)">调整</button></td>
              </tr>
            </tbody>
          </table>
        </div>
        <Pager :total="bills.length" :page="page" @update:page="page = $event" />
      </div>

      <div class="panel">
        <div class="panel-head"><h2>收款记录</h2><span class="small muted">收据随收款自动生成</span></div>
        <div v-if="!payments.length" class="empty">暂无收款</div>
        <div class="table-wrap" v-else>
          <table>
            <thead><tr><th>收款单号</th><th>金额</th><th>方式</th><th>状态</th><th>收据</th><th>时间</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="p in payments" :key="p.id">
                <td class="mono">{{ p.paymentNo }}</td><td>¥{{ money(p.amount) }}</td><td>{{ p.paymentMethod }}</td>
                <td><span class="badge green">{{ p.paymentStatus }}</span></td><td class="mono">{{ p.receiptNo || '-' }}</td><td class="small">{{ p.paidTime }}</td>
                <td><div class="row"><button v-if="p.receiptNo" class="sm" @click="openReceipt(p)">打印</button><button v-if="can('billing')" class="sm" @click="openRefund(p)">退款</button></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

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
