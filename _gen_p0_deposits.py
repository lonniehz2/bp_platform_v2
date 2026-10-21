# -*- coding: utf-8 -*-
"""P0：押金与退款页（建档/收取/抵扣/退款申请-审批-完成）"""
import io
import os

V = r'D:\Work\业务平台开发\frontend\src\views'

PAGE = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">押金与退款</h3>
        <el-tag size="small" type="info">
          余额 = 已收 − 已抵扣 − 已退还
        </el-tag>
        <div class="spacer" />
        <el-button type="success" @click="depVisible = true">押金建档</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="contractId" label="合同" width="130" />
        <el-table-column prop="personId" label="人员" width="110" />
        <el-table-column prop="depositAmount" label="应收" width="100" />
        <el-table-column prop="paidAmount" label="已收" width="100" />
        <el-table-column prop="deductAmount" label="已抵扣" width="100" />
        <el-table-column prop="refundAmount" label="已退还" width="100" />
        <el-table-column prop="balanceAmount" label="余额" width="100" />
        <el-table-column prop="depositStatus" label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.depositStatus === 'REFUNDED' ? 'success'
              : (row.depositStatus === 'DEDUCTED' ? 'warning' : 'info')">
              {{ row.depositStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openAmount(row, 'receive')">收取</el-button>
            <el-button link type="warning" @click="openAmount(row, 'deduct')">抵扣</el-button>
            <el-button link type="success" @click="openRefund(row)">申请退款</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">退款单</h4>
      <el-table :data="refunds" border size="small">
        <el-table-column prop="refundNo" label="退款单号" width="170" />
        <el-table-column prop="contractId" label="合同" width="130" />
        <el-table-column prop="refundAmount" label="金额" width="110" />
        <el-table-column prop="refundType" label="类型" width="110" />
        <el-table-column prop="refundStatus" label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.refundStatus === 'SUCCESS' ? 'success'
              : (row.refundStatus === 'REJECTED' ? 'danger' : 'warning')">
              {{ row.refundStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.refundStatus !== 'PENDING'"
                       @click="approve(row)">批准</el-button>
            <el-button link type="danger" :disabled="row.refundStatus !== 'PENDING'"
                       @click="reject(row)">驳回</el-button>
            <el-button link type="success" :disabled="row.refundStatus !== 'APPROVED'"
                       @click="complete(row)">打款完成</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 押金建档 DepositCreateCmd -->
    <el-dialog v-model="depVisible" title="押金建档" width="500px">
      <el-form :model="dp" label-width="120px">
        <el-form-item label="合同ID"><el-input v-model.number="dp.contractId" />
        </el-form-item>
        <el-form-item label="人员ID"><el-input v-model.number="dp.personId" />
        </el-form-item>
        <el-form-item label="应收押金"><el-input v-model.number="dp.depositAmount" />
        </el-form-item>
        <el-form-item label="实收押金"><el-input v-model.number="dp.paidAmount" />
        </el-form-item>
        <el-form-item label="政策上限"><el-input v-model.number="dp.capAmount" />
          <span class="muted">超上限会告警（成都标准 1000 元）</span>
        </el-form-item>
        <el-form-item label="免收">
          <el-switch v-model="dp.isExempt" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item v-if="dp.isExempt === 1" label="免收原因">
          <el-input v-model="dp.exemptReason" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="depVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doDeposit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 收取/抵扣 AmountCmd -->
    <el-dialog v-model="amtVisible" :title="amtMode === 'receive' ? '收取押金' : '押金抵扣'"
               width="440px">
      <el-form :model="am" label-width="110px">
        <el-form-item label="合同">
          <el-input :model-value="current?.contractId" disabled /></el-form-item>
        <el-form-item label="当前余额">
          <el-input :model-value="current?.balanceAmount" disabled /></el-form-item>
        <el-form-item label="金额"><el-input v-model.number="am.amount" /></el-form-item>
        <el-form-item v-if="amtMode === 'deduct'" label="抵扣原因">
          <el-input v-model="am.reason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="amtVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doAmount">确认</el-button>
      </template>
    </el-dialog>

    <!-- 退款申请 RefundCreateCmd -->
    <el-dialog v-model="refVisible" title="申请退还押金" width="480px">
      <el-form :model="rf" label-width="110px">
        <el-form-item label="合同">
          <el-input :model-value="current?.contractId" disabled /></el-form-item>
        <el-form-item label="可退余额">
          <el-input :model-value="current?.balanceAmount" disabled /></el-form-item>
        <el-form-item label="退款金额">
          <el-input v-model.number="rf.refundAmount" placeholder="必填，不得超余额" />
        </el-form-item>
        <el-form-item label="退款类型">
          <el-select v-model="rf.refundType" style="width:100%">
            <el-option label="押金退还" value="DEPOSIT" />
            <el-option label="多缴退还" value="OVERPAY" />
          </el-select></el-form-item>
        <el-form-item label="退款渠道">
          <el-select v-model="rf.refundChannel" style="width:100%">
            <el-option label="原路退回" value="ORIGINAL" />
            <el-option label="银行转账" value="BANK" />
            <el-option label="现金" value="CASH" />
          </el-select></el-form-item>
        <el-form-item label="退款原因">
          <el-input v-model="rf.refundReason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <el-alert type="warning" :closable="false" show-icon
                title="金额必填（不提供默认值，避免误退）；超余额会被拒绝" />
      <template #footer>
        <el-button @click="refVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRefund">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/modules'
import req from '@/api/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const refunds = ref([])
const current = ref(null)

const depVisible = ref(false)
const dp = reactive({ contractId: null, personId: null, depositAmount: null,
  paidAmount: null, capAmount: 1000, isExempt: 0, exemptReason: '' })

const amtVisible = ref(false)
const amtMode = ref('receive')
const am = reactive({ amount: null, reason: '' })

const refVisible = ref(false)
const rf = reactive({ refundAmount: null, refundType: 'DEPOSIT',
  refundChannel: 'ORIGINAL', refundReason: '' })

async function load() {
  loading.value = true
  try {
    const d = await financeApi.deposits({ pageNum: 1, pageSize: 50 })
    rows.value = d.rows || []
    const r = await req.get('/fin/refunds', { params: { pageNum: 1, pageSize: 50 } })
    refunds.value = r.rows || r || []
  } catch (e) { /* 拦截器已提示 */ } finally { loading.value = false }
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
'''

io.open(os.path.join(V, 'Deposits.vue'), 'w', encoding='utf-8').write(PAGE)
print('  ✓ Deposits.vue 重写（建档/收取/抵扣/退款申请-批准-驳回-完成）')
