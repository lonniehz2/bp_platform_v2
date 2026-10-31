# -*- coding: utf-8 -*-
"""收款时间、收款单详情/核销到账单、账单缴费明细。"""
import io
import os

V = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'views'))
p = os.path.join(V, 'Bills.vue')
s = io.open(p, encoding='utf-8').read()


def rep(old, new, label):
    global s
    if old not in s:
        print('  ! 未匹配:', label)
        return
    s = s.replace(old, new, 1)
    print('  ✔', label)


# 1) 登记收款：收款时间
rep('''        <el-form-item label="交易流水号"><el-input v-model="p.tradeNo" /></el-form-item>''',
    '''        <el-form-item label="收款时间">
          <el-date-picker v-model="p.payTime" type="datetime" style="width:100%"
                          value-format="YYYY-MM-DD HH:mm:ss"
                          placeholder="默认当前时间，可回填历史收款" />
        </el-form-item>
        <el-form-item label="交易流水号"><el-input v-model="p.tradeNo" /></el-form-item>''',
    '收款时间字段')

rep('''const p = reactive({ orgId: null, personId: null, payerName: '', payAmount: null,
  payChannel: 'CASH', tradeNo: '', unknownFlag: 0, remark: '' })''',
    '''function nowText() {
  const d = new Date()
  const z = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + z(d.getMonth() + 1) + '-' + z(d.getDate())
    + ' ' + z(d.getHours()) + ':' + z(d.getMinutes()) + ':' + z(d.getSeconds())
}
const p = reactive({ orgId: null, personId: null, payerName: '', payAmount: null,
  payChannel: 'CASH', payTime: nowText(), tradeNo: '', unknownFlag: 0, remark: '' })''',
    '收款时间默认值')

rep('''function openPay() {
  loadPayOrgs()
  payVisible.value = true
}''',
    '''function openPay() {
  loadPayOrgs()
  p.payTime = nowText()
  payVisible.value = true
}''',
    '打开时刷新默认时间')

# 2) 收款单弹窗宽度/列宽/操作
rep('''    <el-dialog v-model="paymentsVisible" title="收款单" width="900px">''',
    '''    <el-dialog v-model="paymentsVisible" title="收款单" width="1120px" top="5vh">''',
    '收款单宽度')
rep('''        <el-table-column prop="paymentNo" label="收款单号" width="190" />''',
    '''        <el-table-column prop="paymentNo" label="收款单号" width="185" />''',
    '单号列宽')
rep('''        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="!Number(row.remainAmount)"
                       @click="usePayment(row)">用于核销</el-button>
          </template>
        </el-table-column>''',
    '''        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openPaymentDetail(row)">详情</el-button>
            <el-button link type="success" :disabled="!Number(row.remainAmount)"
                       @click="usePayment(row)">核销到账单</el-button>
          </template>
        </el-table-column>''',
    '收款单操作')

# 3) 用于核销：选择账单弹窗 + 详情弹窗
rep('''    <!-- 核销 AllocateCmd -->''',
    '''    <!-- 收款单详情：使用明细 -->
    <el-dialog v-model="payDetailVisible" title="收款单详情" width="820px">
      <el-descriptions v-if="payDetail" :column="2" border size="small">
        <el-descriptions-item label="收款单号">{{ payDetail.paymentNo }}</el-descriptions-item>
        <el-descriptions-item label="缴费人">
          {{ payDetail.payerName || payDetail.personIdName || payDetail.personId || '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="收款金额">{{ payDetail.payAmount }}</el-descriptions-item>
        <el-descriptions-item label="已核销">{{ payDetail.reconciledAmount }}</el-descriptions-item>
        <el-descriptions-item label="余额">{{ payDetail.remainAmount }}</el-descriptions-item>
        <el-descriptions-item label="收款渠道">{{ payDetail.payChannel }}</el-descriptions-item>
        <el-descriptions-item label="收款时间">{{ payDetail.payTime }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          {{ payDetail.payStatusLabel || payDetail.payStatus }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ payDetail.remark || '—' }}</el-descriptions-item>
      </el-descriptions>
      <div style="font-weight:600;margin:12px 0 6px">使用明细（核销到账单）</div>
      <el-table :data="payUsage" border size="small"
                empty-text="尚未核销到任何账单">
        <el-table-column prop="bill_no" label="账单号" width="190" />
        <el-table-column prop="allocate_amount" label="核销金额" width="120" />
        <el-table-column prop="create_time" label="核销时间" />
      </el-table>
    </el-dialog>

    <!-- 收款单核销到账单 -->
    <el-dialog v-model="useVisible" title="核销到账单" width="620px">
      <el-alert type="info" :closable="false" show-icon
                title="选择一张未缴清账单，把本收款单的余额核销进去" />
      <el-form label-width="110px" style="margin-top:10px">
        <el-form-item label="收款单">
          <el-input :model-value="usePaymentRow?.paymentNo" disabled />
        </el-form-item>
        <el-form-item label="可核销余额">
          <el-input :model-value="usePaymentRow?.remainAmount" disabled />
        </el-form-item>
        <el-form-item label="目标账单" required>
          <el-select v-model="useBillId" filterable style="width:100%"
                     placeholder="选择未缴清账单（单号/账期）" @change="onUseBillChange">
            <el-option v-for="b in useBills" :key="b.id"
                       :label="b.billNo + ' · ' + (b.billPeriod || '') + ' · 待缴 ' + b.payableAmount"
                       :value="String(b.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="核销金额">
          <el-input v-model.number="useAmount" placeholder="留空=取余额与待缴较小值" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="useVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="confirmUse">确认核销</el-button>
      </template>
    </el-dialog>

    <!-- 核销 AllocateCmd -->''',
    '收款单详情/核销弹窗')

# 4) 脚本状态与函数
rep('''function usePayment(row) {
  a.paymentId = String(row.id)
  paymentsVisible.value = false
}''',
    '''const payDetailVisible = ref(false)
const payDetail = ref(null)
const payUsage = ref([])
const useVisible = ref(false)
const usePaymentRow = ref(null)
const useBills = ref([])
const useBillId = ref('')
const useAmount = ref(null)

async function openPaymentDetail(row) {
  payDetail.value = row
  payUsage.value = []
  payDetailVisible.value = true
  try {
    const list = await req.get('/fin/payments/' + row.id + '/allocations')
    payUsage.value = list || []
  } catch (e) { payUsage.value = [] }
}

/** 收款单 → 直接核销到账单 */
async function usePayment(row) {
  usePaymentRow.value = row
  useBillId.value = ''
  useAmount.value = null
  useBills.value = []
  paymentsVisible.value = false
  useVisible.value = true
  try {
    const params = { pageNum: 1, pageSize: 100, status: 'UNPAID' }
    if (row.personId) params.personId = row.personId
    const d = await req.get('/fin/bills', { params })
    let rows = (d && d.rows) || []
    if (!rows.length) {
      const all = await req.get('/fin/bills', { params: { pageNum: 1, pageSize: 100, status: 'UNPAID' } })
      rows = (all && all.rows) || []
    }
    useBills.value = rows
  } catch (e) { useBills.value = [] }
}

function onUseBillChange(id) {
  const b = useBills.value.find((x) => String(x.id) === String(id))
  if (!b) return
  const pay = Number(usePaymentRow.value?.remainAmount || 0)
  const due = Number(b.payableAmount || 0)
  useAmount.value = Math.min(pay, due).toFixed(2)
}

async function confirmUse() {
  if (!useBillId.value) { ElMessage.warning('请选择目标账单'); return }
  saving.value = true
  try {
    await financeApi.allocate(useBillId.value && usePaymentRow.value.id, useBillId.value, useAmount.value)
    ElMessage.success('核销成功')
    useVisible.value = false
    load()
    loadPayments()
  } finally { saving.value = false }
}''',
    '收款单逻辑')

# 5) 账单详情：缴费明细
rep('''      <div v-if="explainRows.length" style="margin-top:12px">''',
    '''      <div style="margin-top:12px">
        <div style="font-weight:600;margin-bottom:6px">缴费明细（收款单）</div>
        <el-table :data="billPayments" size="small" border
                  empty-text="暂无收款核销记录">
          <el-table-column prop="payment_no" label="收款单号" width="185" />
          <el-table-column label="缴费人" width="110">
            <template #default="{ row }">{{ row.payer_name || '—' }}</template>
          </el-table-column>
          <el-table-column prop="allocate_amount" label="核销金额" width="110" />
          <el-table-column prop="pay_channel" label="渠道" width="90" />
          <el-table-column prop="pay_time" label="收款时间" />
        </el-table>
      </div>
      <div v-if="explainRows.length" style="margin-top:12px">''',
    '账单缴费明细')

rep('''async function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
  explainRows.value = []''',
    '''const billPayments = ref([])

async function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
  explainRows.value = []
  billPayments.value = []
  try {
    const list = await req.get('/fin/bills/' + row.id + '/payments')
    billPayments.value = list || []
  } catch (e) { billPayments.value = [] }''',
    '账单详情加载缴费')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('Bills 收款单增强完成')
