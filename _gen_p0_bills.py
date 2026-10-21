# -*- coding: utf-8 -*-
"""P0：账单与缴费页（出账/收款登记/核销/减免/取消/逾期扫描）"""
import io
import os

V = r'D:\Work\业务平台开发\frontend\src\views'

BILLS = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">账单与缴费</h3>
        <el-select v-model="q.billStatus" placeholder="状态" clearable
                   style="width:140px" @change="reload">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
        <el-input v-model="q.billPeriod" placeholder="账期 2026-10" clearable
                  style="width:140px" @keyup.enter="reload" />
        <el-button type="primary" @click="reload">查询</el-button>
        <div class="spacer" />
        <el-button type="success" @click="genVisible = true">批量出账</el-button>
        <el-button @click="openPay">登记收款</el-button>
        <el-button @click="scanOverdue">扫描逾期</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="billNo" label="账单号" width="165" />
        <el-table-column prop="payerName" label="缴费人" width="95" />
        <el-table-column prop="billPeriod" label="账期" width="95" />
        <el-table-column prop="billAmount" label="应收" width="90" />
        <el-table-column prop="paidAmount" label="已缴" width="90" />
        <el-table-column prop="waivedAmount" label="减免" width="85" />
        <el-table-column prop="payableAmount" label="待缴" width="90" />
        <el-table-column prop="dueDate" label="截止日" width="105" />
        <el-table-column prop="billStatusLabel" label="状态" width="95">
          <template #default="{ row }">
            <el-tag size="small" :type="row.overdueNow ? 'danger'
              : (row.billStatus === 'PAID' ? 'success' : 'info')">
              {{ row.billStatusLabel || row.billStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="overdueDays" label="逾期" width="70" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openAllocate(row)">核销</el-button>
            <el-button link type="warning" @click="openWaive(row)">减免</el-button>
            <el-button link type="danger" @click="cancelBill(row)">取消</el-button>
            <el-button link @click="dunning(row)">催缴</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="q.pageSize" :current-page="q.pageNum"
                     @current-change="(p) => { q.pageNum = p; load() }" />
    </div>

    <!-- 批量出账 -->
    <el-dialog v-model="genVisible" title="批量出账" width="500px">
      <el-form :model="g" label-width="120px">
        <el-form-item label="组织ID"><el-input v-model.number="g.orgId" /></el-form-item>
        <el-form-item label="账期">
          <el-input v-model="g.billPeriod" placeholder="2026-10" /></el-form-item>
        <el-form-item label="试算（不落库）">
          <el-switch v-model="g.dryRun" /></el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="会按计费项目的 7 种计费方式逐户计算；缺面积/抄表数据会明确报错并指明房源" />
      <template #footer>
        <el-button @click="genVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doGenerate">开始出账</el-button>
      </template>
    </el-dialog>

    <!-- 登记收款 PaymentCreateCmd -->
    <el-dialog v-model="payVisible" title="登记收款" width="520px">
      <el-form :model="p" label-width="110px">
        <el-form-item label="组织ID"><el-input v-model.number="p.orgId" /></el-form-item>
        <el-form-item label="人员ID"><el-input v-model.number="p.personId" /></el-form-item>
        <el-form-item label="缴费人"><el-input v-model="p.payerName" /></el-form-item>
        <el-form-item label="收款金额"><el-input v-model.number="p.payAmount" />
        </el-form-item>
        <el-form-item label="收款渠道">
          <el-select v-model="p.payChannel" style="width:100%">
            <el-option label="现金" value="CASH" />
            <el-option label="银行转账" value="BANK" />
            <el-option label="微信" value="WECHAT" />
            <el-option label="支付宝" value="ALIPAY" />
            <el-option label="POS" value="POS" />
          </el-select></el-form-item>
        <el-form-item label="交易流水号"><el-input v-model="p.tradeNo" /></el-form-item>
        <el-form-item label="来源不明">
          <el-switch v-model="p.unknownFlag" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="p.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doPay">确认收款</el-button>
      </template>
    </el-dialog>

    <!-- 核销 AllocateCmd -->
    <el-dialog v-model="allocVisible" title="账单核销" width="480px">
      <el-alert type="info" :closable="false" show-icon
                title="三重上限：不超收款单余额、不超账单应付、已缴账单不可再核销" />
      <el-form :model="a" label-width="110px" style="margin-top:12px">
        <el-form-item label="账单号">
          <el-input :model-value="current?.billNo" disabled /></el-form-item>
        <el-form-item label="账单待缴">
          <el-input :model-value="current?.payableAmount" disabled /></el-form-item>
        <el-form-item label="收款单ID"><el-input v-model.number="a.paymentId" />
        </el-form-item>
        <el-form-item label="核销金额">
          <el-input v-model.number="a.amount" placeholder="留空=全部待缴" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="allocVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doAllocate">确认核销</el-button>
      </template>
    </el-dialog>

    <!-- 减免 WaiveCmd -->
    <el-dialog v-model="waiveVisible" title="账单减免" width="460px">
      <el-form :model="w" label-width="110px">
        <el-form-item label="账单号">
          <el-input :model-value="current?.billNo" disabled /></el-form-item>
        <el-form-item label="减免金额">
          <el-input v-model.number="w.waiveAmount" placeholder="留空=全部待缴" /></el-form-item>
        <el-form-item label="减免原因">
          <el-input v-model="w.reason" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="waiveVisible = false">取消</el-button>
        <el-button type="warning" :loading="saving" @click="doWaive">确认减免</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/modules'

const statuses = ['UNPAID', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED', 'CANCELLED']
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const q = reactive({ pageNum: 1, pageSize: 20, billStatus: '', billPeriod: '' })
const current = ref(null)

const genVisible = ref(false)
const g = reactive({ orgId: 1, billPeriod: '', dryRun: true })

const payVisible = ref(false)
const p = reactive({ orgId: 1, personId: null, payerName: '', payAmount: null,
  payChannel: 'CASH', tradeNo: '', unknownFlag: 0, remark: '' })

const allocVisible = ref(false)
const a = reactive({ paymentId: null, amount: null })

const waiveVisible = ref(false)
const w = reactive({ waiveAmount: null, reason: '' })

async function load() {
  loading.value = true
  try {
    const d = await financeApi.bills({
      pageNum: q.pageNum, pageSize: q.pageSize,
      billStatus: q.billStatus || undefined,
      billPeriod: q.billPeriod || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}
function reload() { q.pageNum = 1; load() }

async function doGenerate() {
  saving.value = true
  try {
    const r = await financeApi.generate({ ...g })
    ElMessage.success('出账完成：生成 ' + (r?.generated ?? r?.count ?? '-') + ' 张')
    genVisible.value = false; load()
  } finally { saving.value = false }
}

function openPay() { payVisible.value = true }
async function doPay() {
  if (!p.payAmount || p.payAmount <= 0) { ElMessage.warning('收款金额必须大于 0'); return }
  saving.value = true
  try {
    await financeApi.createPayment({ ...p })
    ElMessage.success('收款已登记')
    payVisible.value = false
  } finally { saving.value = false }
}

function openAllocate(row) {
  current.value = row; a.paymentId = null; a.amount = null
  allocVisible.value = true
}
async function doAllocate() {
  if (!a.paymentId) { ElMessage.warning('请填写收款单ID'); return }
  saving.value = true
  try {
    await financeApi.allocate(a.paymentId, current.value.id, a.amount)
    ElMessage.success('核销成功')
    allocVisible.value = false; load()
  } finally { saving.value = false }
}

function openWaive(row) {
  current.value = row; w.waiveAmount = null; w.reason = ''
  waiveVisible.value = true
}
async function doWaive() {
  if (!w.reason) { ElMessage.warning('请填写减免原因'); return }
  saving.value = true
  try {
    await financeApi.waive(current.value.id, { ...w })
    ElMessage.success('减免成功')
    waiveVisible.value = false; load()
  } finally { saving.value = false }
}

async function cancelBill(row) {
  const { value } = await ElMessageBox.prompt('请输入取消原因', '取消账单')
  await financeApi.cancelBill(row.id, value)
  ElMessage.success('账单已取消'); load()
}

async function dunning(row) {
  await financeApi.arrears({ billId: row.id })
  ElMessage.success('已发起催缴（可在催缴管理查看）')
}

async function scanOverdue() {
  await financeApi.scanOverdue()
  ElMessage.success('逾期扫描完成'); load()
}

onMounted(load)
</script>
'''

io.open(os.path.join(V, 'Bills.vue'), 'w', encoding='utf-8').write(BILLS)
print('  ✓ Bills.vue 重写（批量出账/收款登记/核销/减免/取消/逾期扫描/催缴）')
