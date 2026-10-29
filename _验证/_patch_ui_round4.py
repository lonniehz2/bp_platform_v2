# -*- coding: utf-8 -*-
"""合同变更入口/列/中文；换房状态校验；账单组织选择；押金自动带出。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return s


# ================= 3) 合同变更入口 =================
p = os.path.join(V, 'Contracts.vue')
s = io.open(p, encoding='utf-8').read()
if 'openChangeDlg' not in s:
    s = s.replace('''            <el-button link type="warning" @click="openSwap(row)">换房</el-button>''',
                  '''            <el-button link type="warning" @click="openSwap(row)">换房</el-button>
            <el-button v-if="['EFFECTIVE','RENEWING'].includes(row.contractStatus)"
                       link type="primary" @click="openChangeDlg(row)">发起变更</el-button>''', 1)
    s = s.replace('''    <!-- 快捷签约 -->''', '''    <!-- 发起合同变更 -->
    <el-dialog v-model="chgVisible" title="发起合同变更" width="560px">
      <el-form :model="chg" label-width="110px">
        <el-form-item label="合同"><el-input :model-value="chg.contractNo" disabled /></el-form-item>
        <el-form-item label="变更类型">
          <el-select v-model="chg.changeType" style="width:100%">
            <el-option label="调租" value="RENT_ADJUST" />
            <el-option label="租期变更" value="PERIOD" />
            <el-option label="续签" value="RENEW" />
            <el-option label="其他" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item label="新月租金">
          <el-input v-model.number="chg.newMonthlyRent" placeholder="调租时填写" />
        </el-form-item>
        <el-form-item label="新止租日">
          <el-date-picker v-model="chg.newLeaseEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="生效日期">
          <el-date-picker v-model="chg.effectiveDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="变更原因">
          <el-input v-model="chg.changeReason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="提交后进入「合同变更」审批；批准且到生效日后自动写回合同。" />
      <template #footer>
        <el-button @click="chgVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doChange">提交</el-button>
      </template>
    </el-dialog>

    <!-- 快捷签约 -->''', 1)
    if 'const chgVisible' not in s:
        s = s.replace('''const swapVisible = ref(false)''', '''const chgVisible = ref(false)
const chg = reactive({ contractId: null, contractNo: '', changeType: 'RENT_ADJUST',
  newMonthlyRent: null, newLeaseEnd: '', effectiveDate: '', changeReason: '' })

function openChangeDlg(row) {
  Object.assign(chg, { contractId: row.id, contractNo: row.contractNo,
    changeType: 'RENT_ADJUST', newMonthlyRent: null, newLeaseEnd: '',
    effectiveDate: new Date().toISOString().slice(0, 10), changeReason: '' })
  chgVisible.value = true
}

async function doChange() {
  if (!chg.contractId) { ElMessage.warning('缺少合同'); return }
  saving.value = true
  try {
    await req.post('/contracts/' + chg.contractId + '/changes', {
      changeType: chg.changeType, changeReason: chg.changeReason || undefined,
      newMonthlyRent: chg.newMonthlyRent || undefined,
      newLeaseEnd: chg.newLeaseEnd || undefined,
      effectiveDate: chg.effectiveDate || undefined
    })
    ElMessage.success('变更申请已提交，等待审批')
    chgVisible.value = false
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '提交失败')
  } finally { saving.value = false }
}

const swapVisible = ref(false)''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 合同变更入口')

# ================= 4) 换房：仅履约中自动带入 =================
p = os.path.join(V, 'Exchanges.vue')
patch(p, [
    ('''    const ct = await req.get('/contracts/active-by-person/' + pid)
    if (ct) {
      form.oldContractId = ct.id
      form.oldHouseId = ct.houseId
      auto.contractNo = ct.contractNo
      auto.houseName = ct.houseIdName || ct.houseId
      auto.orgName = ct.orgIdName || ct.orgId
    }''',
     '''    const ct = await req.get('/contracts/active-by-person/' + pid)
    if (ct && ct.contractStatus === 'EFFECTIVE') {
      form.oldContractId = ct.id
      form.oldHouseId = ct.houseId
      auto.contractNo = ct.contractNo
      auto.houseName = ct.houseIdName || ct.houseId
      auto.orgName = ct.orgIdName || ct.orgId
    } else if (ct) {
      ElMessage.warning('该人员合同当前为「' + (ct.contractStatusLabel || ct.contractStatus)
        + '」，仅履约中合同可发起换房')
    } else {
      ElMessage.warning('该人员没有生效中的合同，不能发起换房')
    }''', '换房合同状态校验'),
])

# ================= 6) 合同变更列表列 + 中文 =================
p = os.path.join(V, 'ContractChanges.vue')
s = io.open(p, encoding='utf-8').read()
if '房源' not in s:
    s = s.replace('''      <el-table-column prop="changeNo" label="变更号" width="170" />''',
                  '''      <el-table-column prop="changeNo" label="变更号" width="170" />
      <el-table-column prop="houseName" label="房源" width="150" />
      <el-table-column prop="lesseeName" label="承租人" width="110" />
      <el-table-column label="变更前" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ beforeText(row) }}</template>
      </el-table-column>
      <el-table-column label="变更后" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">{{ afterText(row) }}</template>
      </el-table-column>
      <el-table-column prop="changeReason" label="变更原因" min-width="140" show-overflow-tooltip />''', 1)
    # 展开区域用中文
    s = s.replace('''        <template #default="{ row }"><DetailView :row="row" /></template>''',
                  '''        <template #default="{ row }">
          <div style="display:flex;gap:24px;padding:8px 12px">
            <div><b>变更前</b><div class="kv">{{ beforeText(row) }}</div></div>
            <div><b>变更后</b><div class="kv">{{ afterText(row) }}</div></div>
          </div>
        </template>''', 1)
    if 'function beforeText' not in s:
        s = s.replace('''const changeVisible = ref(false)''', '''function kvText(raw) {
  if (raw == null || raw === '') return '—'
  let obj = raw
  if (typeof raw === 'string') {
    try { obj = JSON.parse(raw) } catch (e) { return raw }
  }
  if (!obj || typeof obj !== 'object') return String(obj)
  const label = { monthlyRent: '月租金', leaseEnd: '止租日', leaseStart: '起租日',
    lesseePersonId: '承租人ID', lesseeName: '承租人', depositAmount: '押金',
    contractNo: '合同号', houseId: '房源', remark: '备注' }
  return Object.keys(obj).map((k) => (label[k] || k) + '：' + obj[k]).join('；')
}
function beforeText(row) { return kvText(row.beforeJson ?? row.before) }
function afterText(row) { return kvText(row.afterJson ?? row.after) }

const changeVisible = ref(false)''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 变更列表列/中文')

# ================= 7) 登记收款组织搜索 =================
p = os.path.join(V, 'Bills.vue')
s = io.open(p, encoding='utf-8').read()
if 'payOrgs' not in s:
    s = s.replace('''        <el-form-item label="组织ID"><el-input v-model="p.orgId" /></el-form-item>''',
                  '''        <el-form-item label="组织">
          <el-select v-model="p.orgId" filterable clearable style="width:100%"
                     placeholder="按名称搜索组织">
            <el-option v-for="o in payOrgs" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>''', 1)
    if 'const payOrgs' not in s:
        s = s.replace('''const payVisible = ref(false)''', '''const payVisible = ref(false)
const payOrgs = ref([])
async function loadPayOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    payOrgs.value = (d && d.rows) || []
  } catch (e) { payOrgs.value = [] }
}''', 1)
        s = s.replace('''function openPay() {''', '''function openPay() {
  loadPayOrgs()''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 收款组织下拉')

# ================= 9) 押金自动带出 =================
p = os.path.join(V, 'Deposits.vue')
s = io.open(p, encoding='utf-8').read()
if 'fillFromContract' not in s:
    s = s.replace('''        <el-form-item label="合同ID"><el-input v-model="dp.contractId" />''',
                  '''        <el-form-item label="合同ID"><el-input v-model="dp.contractId"
                     @blur="fillFromContract" />''', 1)
    if 'watch(' not in s and 'fillFromContract' in s:
        s = s.replace("import { ref, reactive, onMounted } from 'vue'",
                      "import { ref, reactive, watch, onMounted } from 'vue'", 1)
        s = s.replace('''const dp = reactive({ contractId: null, personId: null, depositAmount: null,
  paidAmount: null, capAmount: 1000, isExempt: 0, exemptReason: '' })''',
                      '''const dp = reactive({ contractId: null, personId: null, depositAmount: null,
  paidAmount: 0, capAmount: 1000, isExempt: 0, exemptReason: '' })

async function fillFromContract() {
  if (!dp.contractId) return
  try {
    const c = await req.get('/contracts/' + dp.contractId)
    if (c) {
      dp.personId = c.lesseePersonId
      if (c.depositAmount != null) dp.depositAmount = c.depositAmount
    }
  } catch (e) {
    ElMessage.warning('未找到该合同，请检查合同ID')
  }
}''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 押金自动带出')
