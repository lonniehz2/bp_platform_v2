# -*- coding: utf-8 -*-
"""账单页：收款单入口 + 核销改选收款单。"""
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


# 1) 工具栏：收款单入口
rep('''        <el-button @click="openPay">登记收款</el-button>''',
    '''        <el-button @click="openPay">登记收款</el-button>
        <el-button plain @click="openPayments" data-testid="bill-payments">收款单</el-button>''',
    '收款单按钮')

# 2) 核销：收款单改为下拉选择
rep('''        <el-form-item label="收款单ID"><el-input v-model="a.paymentId" />
        </el-form-item>''',
    '''        <el-form-item label="收款单" required>
          <el-select v-model="a.paymentId" filterable style="width:100%"
                     placeholder="选择待核销收款单（单号/缴费人）">
            <el-option v-for="x in openPaymentsList" :key="x.id"
                       :label="x.paymentNo + ' · ' + (x.payerName || '—') + ' · 余额 ' + (x.remainAmount ?? 0)"
                       :value="String(x.id)" />
          </el-select>
          <span class="muted" style="font-size:12px">
            没有收款单？先点顶部「登记收款」，再回到本页核销
          </span>
        </el-form-item>''',
    '核销选择收款单')

# 3) 收款单列表弹窗（插在核销弹窗前）
rep('''    <!-- 核销 AllocateCmd -->''',
    '''    <!-- 收款单列表 -->
    <el-dialog v-model="paymentsVisible" title="收款单" width="900px">
      <div class="toolbar" style="margin-bottom:8px">
        <el-input v-model="payKeyword" placeholder="收款单号" clearable style="width:240px"
                  @keyup.enter="loadPayments" />
        <el-button type="primary" @click="loadPayments">查询</el-button>
        <div class="spacer" />
        <el-button @click="openPay">登记收款</el-button>
      </div>
      <el-table :data="payments" border size="small" max-height="420"
                empty-text="暂无收款单，点击「登记收款」新增">
        <el-table-column prop="paymentNo" label="收款单号" width="190" />
        <el-table-column prop="payerName" label="缴费人" width="120" />
        <el-table-column prop="payAmount" label="收款金额" width="110" />
        <el-table-column prop="reconciledAmount" label="已核销" width="110" />
        <el-table-column prop="remainAmount" label="余额" width="110" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">{{ row.payStatusLabel || row.payStatus }}</template>
        </el-table-column>
        <el-table-column prop="payTime" label="收款时间" width="170" />
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="!Number(row.remainAmount)"
                       @click="usePayment(row)">用于核销</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:10px" layout="total, prev, pager, next"
                     :total="+payTotal || 0" :page-size="payPageSize"
                     :current-page="payPageNum"
                     @current-change="(p) => { payPageNum = p; loadPayments() }" />
    </el-dialog>

    <!-- 核销 AllocateCmd -->''',
    '收款单弹窗')

# 4) 逻辑
rep('''const a = reactive({ paymentId: null, amount: null })''',
    '''const a = reactive({ paymentId: null, amount: null })
const paymentsVisible = ref(false)
const payments = ref([])
const openPaymentsList = ref([])
const payKeyword = ref('')
const payPageNum = ref(1)
const payPageSize = ref(50)
const payTotal = ref(0)

async function loadPayments() {
  try {
    const d = await req.get('/fin/payments', {
      params: { pageNum: payPageNum.value, pageSize: payPageSize.value,
        keyword: payKeyword.value || undefined }
    })
    payments.value = (d && d.rows) || []
    payTotal.value = Number((d && d.total) || 0)
    openPaymentsList.value = payments.value.filter((x) => Number(x.remainAmount) > 0)
  } catch (e) { payments.value = []; openPaymentsList.value = [] }
}

async function openPayments() {
  payPageNum.value = 1
  await loadPayments()
  paymentsVisible.value = true
}

function usePayment(row) {
  a.paymentId = String(row.id)
  paymentsVisible.value = false
}''',
    '收款单逻辑')

rep('''function openAllocate(row) {
  current.value = row; a.paymentId = null; a.amount = null
  allocVisible.value = true
}''',
    '''function openAllocate(row) {
  current.value = row; a.paymentId = null; a.amount = null
  loadPayments()
  allocVisible.value = true
}''',
    '打开核销加载收款单')

# 5) 登记收款后提示单号
rep('''    await financeApi.createPayment({ ...p })
    ElMessage.success('收款已登记')
    payVisible.value = false''',
    '''    const created = await financeApi.createPayment({ ...p })
    const no = created && (created.paymentNo || created.id)
    ElMessage.success('收款已登记' + (no ? ('：' + no + '（可在「收款单」查看）') : ''))
    payVisible.value = false
    loadPayments()''',
    '收款单号提示')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('Bills 收款单入口完成')
