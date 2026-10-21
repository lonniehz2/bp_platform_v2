# -*- coding: utf-8 -*-
"""P0：合同（新建/签约/续签/终止/取消）+ 账单（出账/收款/核销/减免/取消）表单页"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
V = os.path.join(BASE, 'src', 'views')

# ---------- 1) API 补全 ----------
p = os.path.join(BASE, 'src', 'api', 'modules.js')
s = io.open(p, encoding='utf-8').read()

if 'contractApi.sign' not in s:
    s = s.replace(
        "  expireDue: () => req.post('/contracts/expire-due')",
        "  expireDue: () => req.post('/contracts/expire-due'),\n"
        "  create: (data) => req.post('/contracts', data),\n"
        "  // 签名接口：SignCmd{signVendor, signFileUrl, signFlowId, reason}\n"
        "  sign: (id, data) => req.post(`/contracts/${id}/sign`, data),\n"
        "  // 续签：RenewCmd{newLeaseEnd, newMonthlyRent}\n"
        "  renew: (id, data) => req.post(`/contracts/${id}/renew`, data),\n"
        "  terminate: (id, data) => req.post(`/contracts/${id}/terminate`, data),\n"
        "  cancel: (id, reason) => req.post(`/contracts/${id}/cancel`, { reason })")
if 'createPayment' not in s:
    s = s.replace(
        "  payments: (params) => req.get('/fin/payments', { params }),",
        "  payments: (params) => req.get('/fin/payments', { params }),\n"
        "  createPayment: (data) => req.post('/fin/payments', data),\n"
        "  cancelBill: (id, reason) => req.post(`/fin/bills/${id}/cancel`, { reason }),\n"
        "  billGenerateBatch: (data) => req.post('/fin/bills/generate-batch', data),")
io.open(p, 'w', encoding='utf-8').write(s)
print('  ✓ modules.js 已补合同签名/续签/终止/取消 + 收款登记/账单取消')

# ---------- 2) 合同页（含 5 个操作） ----------
CONTRACTS = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">合同管理</h3>
        <el-select v-model="q.contractStatus" placeholder="状态" clearable
                   style="width:150px" @change="reload">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="reload">查询</el-button>
        <div class="spacer" />
        <el-button type="success" @click="openCreate">新建合同</el-button>
        <el-button @click="expireDue">到期批量处理</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="contractNo" label="合同号" width="170" />
        <el-table-column prop="lesseeName" label="承租人" width="100" />
        <el-table-column prop="houseAddress" label="房屋" min-width="170" />
        <el-table-column prop="leaseStart" label="起租" width="105" />
        <el-table-column prop="leaseEnd" label="止租" width="105" />
        <el-table-column prop="monthlyRent" label="月租" width="95" />
        <el-table-column prop="contractStatusLabel" label="状态" width="105">
          <template #default="{ row }">
            <el-tag size="small" :type="row.expiringSoon ? 'warning' : 'info'">
              {{ row.contractStatusLabel || row.contractStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="290" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openSign(row)">签约</el-button>
            <el-button link @click="openRenew(row)">续签</el-button>
            <el-button link type="warning" @click="openTerminate(row)">终止</el-button>
            <el-button link type="danger" @click="cancel(row)">取消</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="q.pageSize" :current-page="q.pageNum"
                     @current-change="(p) => { q.pageNum = p; load() }" />
    </div>

    <!-- 新建合同 ContractCreateCmd -->
    <el-dialog v-model="createVisible" title="新建合同" width="680px">
      <el-form :model="c" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="合同类型">
            <el-select v-model="c.contractType" style="width:100%">
              <el-option label="公租房" value="PUBLIC_RENTAL" />
              <el-option label="保租房" value="AFFORDABLE" />
              <el-option label="人才公寓" value="TALENT" />
              <el-option label="廉租房" value="LOW_RENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="出租组织ID">
            <el-input v-model.number="c.orgId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="承租人ID">
            <el-input v-model.number="c.lesseePersonId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="承租人姓名">
            <el-input v-model="c.lesseeName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="联系电话">
            <el-input v-model="c.lesseePhone" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="证件号">
            <el-input v-model="c.lesseeIdCardMask" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="房源ID">
            <el-input v-model.number="c.houseId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="空间ID">
            <el-input v-model.number="c.spaceId" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="房屋地址">
            <el-input v-model="c.houseAddress" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="建筑面积">
            <el-input v-model.number="c.houseArea" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="起租日">
            <el-date-picker v-model="c.leaseStart" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="止租日">
            <el-date-picker v-model="c.leaseEnd" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="月租金">
            <el-input v-model.number="c.monthlyRent" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="租金单价">
            <el-input v-model.number="c.rentPrice" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="押金">
            <el-input v-model.number="c.depositAmount" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="月补贴">
            <el-input v-model.number="c.subsidyAmount" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="付款周期">
            <el-select v-model="c.payCycle" style="width:100%">
              <el-option label="月付" value="MONTH" />
              <el-option label="季付" value="QUARTER" />
              <el-option label="半年付" value="HALF_YEAR" />
              <el-option label="年付" value="YEAR" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="付款日">
            <el-input v-model.number="c.payDay" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="关联配租单ID">
            <el-input v-model.number="c.allocationId" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="备注">
            <el-input v-model="c.remark" type="textarea" :rows="2" />
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <el-alert type="warning" :closable="false" show-icon
                title="月租金/押金/补贴会按计费规则出账；关联配租单会做公示完成校验" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 签约 SignCmd -->
    <el-dialog v-model="signVisible" title="合同签约" width="480px">
      <el-form :model="sg" label-width="110px">
        <el-form-item label="签署方式">
          <el-select v-model="sg.signVendor" style="width:100%">
            <el-option label="线下纸质" value="OFFLINE" />
            <el-option label="电子签章" value="ESIGN" />
            <el-option label="CA证书" value="CA" />
          </el-select></el-form-item>
        <el-form-item label="签署文件URL">
          <el-input v-model="sg.signFileUrl" /></el-form-item>
        <el-form-item label="签署流程ID">
          <el-input v-model="sg.signFlowId" /></el-form-item>
        <el-form-item label="备注">
          <el-input v-model="sg.reason" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="signVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSign">确认签约</el-button>
      </template>
    </el-dialog>

    <!-- 续签 RenewCmd -->
    <el-dialog v-model="renewVisible" title="合同续签" width="460px">
      <el-form :model="rn" label-width="110px">
        <el-form-item label="新止租日">
          <el-date-picker v-model="rn.newLeaseEnd" type="date"
                          value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="新月租金">
          <el-input v-model.number="rn.newMonthlyRent" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renewVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRenew">确认续签</el-button>
      </template>
    </el-dialog>

    <!-- 终止 -->
    <el-dialog v-model="termVisible" title="终止合同" width="460px">
      <el-form :model="tm" label-width="110px">
        <el-form-item label="终止类型">
          <el-select v-model="tm.terminateType" style="width:100%">
            <el-option label="协商终止" value="AGREEMENT" />
            <el-option label="违约终止" value="BREACH" />
            <el-option label="到期终止" value="EXPIRE" />
          </el-select></el-form-item>
        <el-form-item label="终止原因">
          <el-input v-model="tm.reason" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="termVisible = false">取消</el-button>
        <el-button type="danger" :loading="saving" @click="doTerminate">确认终止</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { contractApi } from '@/api/modules'

const statuses = ['DRAFT', 'PENDING_SIGN', 'EFFECTIVE', 'CHANGING', 'TERMINATED', 'EXPIRED']
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const q = reactive({ pageNum: 1, pageSize: 20, contractStatus: '' })

const createVisible = ref(false)
const signVisible = ref(false)
const renewVisible = ref(false)
const termVisible = ref(false)
const current = ref(null)

const c = reactive({ contractType: 'PUBLIC_RENTAL', orgId: 1, lesseePersonId: null,
  lesseeName: '', lesseePhone: '', lesseeIdCardMask: '', houseId: null, spaceId: null,
  houseAddress: '', houseArea: null, leaseStart: '', leaseEnd: '', rentPrice: null,
  rentUnit: 'MONTH', monthlyRent: null, depositAmount: null, subsidyAmount: 0,
  payCycle: 'MONTH', payDay: 5, allocationId: null, remark: '' })
const sg = reactive({ signVendor: 'OFFLINE', signFileUrl: '', signFlowId: '', reason: '' })
const rn = reactive({ newLeaseEnd: '', newMonthlyRent: null })
const tm = reactive({ terminateType: 'AGREEMENT', reason: '' })

async function load() {
  loading.value = true
  try {
    const d = await contractApi.page({
      pageNum: q.pageNum, pageSize: q.pageSize,
      contractStatus: q.contractStatus || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}
function reload() { q.pageNum = 1; load() }

function openCreate() { createVisible.value = true }
async function doCreate() {
  if (!c.lesseePersonId || !c.houseId || !c.leaseStart || !c.leaseEnd) {
    ElMessage.warning('承租人、房源、起止租日为必填'); return
  }
  saving.value = true
  try {
    await contractApi.create({ ...c })
    ElMessage.success('合同已创建')
    createVisible.value = false; load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}

function openSign(row) { current.value = row; signVisible.value = true }
async function doSign() {
  saving.value = true
  try {
    await contractApi.sign(current.value.id, { ...sg })
    ElMessage.success('签约成功')
    signVisible.value = false; load()
  } finally { saving.value = false }
}

function openRenew(row) {
  current.value = row
  rn.newLeaseEnd = row.leaseEnd; rn.newMonthlyRent = row.monthlyRent
  renewVisible.value = true
}
async function doRenew() {
  saving.value = true
  try {
    await contractApi.renew(current.value.id, { ...rn })
    ElMessage.success('续签成功')
    renewVisible.value = false; load()
  } finally { saving.value = false }
}

function openTerminate(row) {
  current.value = row; tm.reason = ''; termVisible.value = true
}
async function doTerminate() {
  if (!tm.reason) { ElMessage.warning('请填写终止原因'); return }
  saving.value = true
  try {
    await contractApi.terminate(current.value.id, { ...tm })
    ElMessage.success('合同已终止')
    termVisible.value = false; load()
  } finally { saving.value = false }
}

async function cancel(row) {
  const { value } = await ElMessageBox.prompt('请输入取消原因', '取消合同')
  await contractApi.cancel(row.id, value)
  ElMessage.success('已取消'); load()
}

async function expireDue() {
  const r = await contractApi.expireDue()
  ElMessage.success('到期处理完成：' + (r?.count ?? r ?? '已执行'))
  load()
}

onMounted(load)
</script>
'''

io.open(os.path.join(V, 'Contracts.vue'), 'w', encoding='utf-8').write(CONTRACTS)
print('  ✓ Contracts.vue 重写（新建/签约/续签/终止/取消/到期处理）')
