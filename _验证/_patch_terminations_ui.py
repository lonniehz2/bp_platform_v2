# -*- coding: utf-8 -*-
"""退租页：筛选/列/表单自动带出/查验-结算-结算单-办结。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'Terminations.vue')
s = io.open(p, encoding='utf-8').read()


def rep(old, new, label):
    global s
    if old not in s:
        print('  ! 未匹配:', label)
        return
    s = s.replace(old, new, 1)
    print('  ✔', label)


# 1) 筛选
rep('''      <template #more>
        <ContractSelect v-model="tf.contractId" width="200px" testid="contract-select" />''',
    '''      <template #more>
        <OrgSelect v-model="tf.orgId" width="200px" testid="term-org" />
        <HouseSelect v-model="tf.houseId" width="200px" testid="term-house" />
        <el-input v-model="tf.keyword" placeholder="退租单号/承租人" clearable
                  style="width:200px" data-testid="term-keyword" />
        <ContractSelect v-model="tf.contractId" width="200px" testid="contract-select" />''',
    '筛选栏')

# 2) 列
rep('''      <el-table-column prop="terminationType" label="类型" width="120">''',
    '''      <el-table-column prop="orgName" label="组织" width="150" />
      <el-table-column prop="houseName" label="房源" width="140" />
      <el-table-column prop="lesseeName" label="承租人" width="110" />
      <el-table-column label="租期" width="180">
        <template #default="{ row }">{{ row.leaseStart }} ~ {{ row.leaseEnd }}</template>
      </el-table-column>
      <el-table-column prop="monthlyRent" label="月租" width="100" />
      <el-table-column prop="depositAmount" label="押金" width="100" />
      <el-table-column prop="terminationType" label="类型" width="120">''', '列表列')

# 3) 操作
rep('''          <el-button link @click="openInspect(row)">查验</el-button>
          <el-button link type="warning" @click="openSettle(row)">结算</el-button>
          <el-button link type="danger" @click="openEnforce(row)">强制腾退</el-button>
          <el-button link type="success" @click="openRelease(row)">释放房源</el-button>
          <el-button link type="success" @click="doComplete(row)">办结</el-button>''',
    '''          <el-button v-if="row.inspectStatus && row.inspectStatus !== 'PENDING'"
                     link type="success" @click="openDetail(row)">已查验</el-button>
          <el-button v-else link @click="openInspect(row)">查验</el-button>
          <el-button v-if="row.settleStatus === 'SETTLED'" link type="success"
                     @click="openDetail(row)">结算单</el-button>
          <el-button v-else link type="warning" :disabled="!row.inspectStatus
                     || row.inspectStatus === 'PENDING'" @click="openSettle(row)">结算</el-button>
          <el-button v-if="row.settleStatus === 'SETTLED'" link type="success"
                     @click="doComplete(row)">办结</el-button>''', '操作列')

# 4) 创建表单
rep('''        <el-form-item label="合同ID"><el-input v-model="c.contractId" /></el-form-item>
        <el-form-item label="房源ID"><el-input v-model="c.houseId" /></el-form-item>
        <el-form-item label="人员ID"><PersonPicker v-model="c.personId" width="240px" testid="person-picker" /></el-form-item>''',
    '''        <el-form-item label="人员" required>
          <PersonPicker v-model="c.personId" width="260px" testid="person-picker" />
        </el-form-item>
        <el-form-item label="原合同">
          <el-input :model-value="auto.contractNo || c.contractId" disabled />
        </el-form-item>
        <el-form-item label="原房源">
          <el-input :model-value="auto.houseName || c.houseId" disabled />
        </el-form-item>
        <el-form-item label="组织">
          <el-input :model-value="auto.orgName" disabled />
        </el-form-item>
        <el-form-item label="租期">
          <el-input :model-value="auto.leaseStart + ' ~ ' + auto.leaseEnd" disabled />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="月租">
            <el-input :model-value="auto.monthlyRent" disabled /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="押金">
            <el-input :model-value="auto.depositAmount" disabled /></el-form-item></el-col>
        </el-row>
        <el-alert v-if="c.personId && !auto.contractNo" type="warning" :closable="false"
                  title="该人员当前没有生效合同，无法发起退租" style="margin-bottom:8px" />''',
    '创建表单自动带出')

# 5) 结算弹窗（预览+公式+合计）
rep('''    <el-dialog v-model="settleVisible" title="退租结算" width="460px">
      <el-form :model="st" label-width="130px">
        <el-form-item label="押金退还额">
          <el-input v-model.number="st.depositRefund" /></el-form-item>
        <el-form-item label="欠费扣缴额">
          <el-input v-model.number="st.arrearsAmount" /></el-form-item>
      </el-form>''',
    '''    <el-dialog v-model="settleVisible" title="退租结算" width="520px">
      <el-alert type="info" :closable="false" show-icon
                :title="preview.formula || '应退合计 = 押金 − 欠费 − 损坏赔偿'" style="margin-bottom:10px" />
      <el-form :model="st" label-width="130px">
        <el-form-item label="押金">
          <el-input :model-value="preview.depositAmount" disabled /></el-form-item>
        <el-form-item label="欠费扣缴">
          <el-input v-model.number="st.arrearsAmount" /></el-form-item>
        <el-form-item label="损坏赔偿">
          <el-input :model-value="preview.damageAmount" disabled /></el-form-item>
        <el-form-item label="应退合计">
          <el-input :model-value="totalPreview" disabled /></el-form-item>
      </el-form>''', '结算弹窗')

# 6) 脚本 imports / 状态
rep('''import ContractSelect from '@/components/ContractSelect.vue\'''',
    '''import ContractSelect from '@/components/ContractSelect.vue'
import OrgSelect from '@/components/OrgSelect.vue'
import HouseSelect from '@/components/HouseSelect.vue\'''', '导入')

rep('''const tf = reactive({ status: '', type: '', contractId: '' })''',
    '''const tf = reactive({ status: '', type: '', contractId: '', orgId: '',
  houseId: '', keyword: '' })''', 'tf 筛选')

rep('''      contractId: tf.contractId || undefined
    })''', '''      contractId: tf.contractId || undefined,
      orgId: tf.orgId || undefined,
      houseId: tf.houseId || undefined,
      keyword: tf.keyword || undefined
    })''', 'load 参数')

rep('''  tf.contractId = ''
  resetAndLoad()''', '''  tf.contractId = ''
  tf.orgId = ''
  tf.houseId = ''
  tf.keyword = ''
  resetAndLoad()''', 'resetQuery')

rep('''const st = reactive({ depositRefund: null, arrearsAmount: null })''',
    '''const st = reactive({ depositRefund: null, arrearsAmount: null })
const auto = reactive({ contractNo: '', houseName: '', orgName: '', leaseStart: '',
  leaseEnd: '', monthlyRent: '', depositAmount: '' })
const preview = reactive({ depositAmount: 0, arrearsAmount: 0, damageAmount: 0,
  totalAmount: 0, formula: '' })
const totalPreview = computed(() => {
  const dep = Number(preview.depositAmount || 0)
  const arr = Number(st.arrearsAmount || 0)
  const dmg = Number(preview.damageAmount || 0)
  return (dep - arr - dmg).toFixed(2)
})''', '预览状态')

# computed import
rep("import { ref, reactive, onMounted } from 'vue'",
    "import { ref, reactive, computed, watch, onMounted } from 'vue'", 'computed/watch')

# 7) 人员选择自动带出
rep('''async function load() {''',
    '''watch(() => c.personId, async (pid) => {
  Object.assign(auto, { contractNo: '', houseName: '', orgName: '', leaseStart: '',
    leaseEnd: '', monthlyRent: '', depositAmount: '' })
  c.contractId = null
  c.houseId = null
  if (!pid) return
  try {
    const ct = await req.get('/contracts/active-by-person/' + pid)
    if (!ct) return
    c.contractId = ct.id
    c.houseId = ct.houseId
    auto.contractNo = ct.contractNo
    auto.houseName = ct.houseIdName || ct.houseId
    auto.orgName = ct.orgIdName || ct.orgId
    auto.leaseStart = ct.leaseStart
    auto.leaseEnd = ct.leaseEnd
    auto.monthlyRent = ct.monthlyRent
    auto.depositAmount = ct.depositAmount
  } catch (e) { /* 无合同保持空 */ }
})

function openCreate() {
  Object.assign(c, { contractId: null, houseId: null, personId: null,
    terminationType: 'NORMAL', planExitDate: '', exitReason: '',
    transitionMonths: 3, transitionRentMultiplier: 1.5, relocationMonths: null })
  Object.assign(auto, { contractNo: '', houseName: '', orgName: '', leaseStart: '',
    leaseEnd: '', monthlyRent: '', depositAmount: '' })
  createVisible.value = true
}

async function load() {''', '自动带出/打开创建')

# 8) 结算预览
rep('''function openSettle(row) { current.value = row; settleVisible.value = true }''',
    '''async function openSettle(row) {
  current.value = row
  st.depositRefund = null
  st.arrearsAmount = null
  try {
    const pv = await req.get('/terminations/' + row.id + '/settle-preview')
    Object.assign(preview, pv || {})
    st.arrearsAmount = pv?.arrearsAmount ?? 0
    st.depositRefund = pv?.depositAmount ?? 0
  } catch (e) { ElMessage.error('结算预览加载失败') }
  settleVisible.value = true
}''', '结算预览')

# 9) 创建按钮 & 结算传参
rep('''<el-button type="success" @click="createVisible = true">发起退租</el-button>''',
    '''<el-button type="success" @click="openCreate">发起退租</el-button>''', '创建按钮')
rep('''    await req.post(`/terminations/${current.value.id}/settle`, { ...st })''',
    '''    await req.post(`/terminations/${current.value.id}/settle`,
      { depositRefund: st.depositRefund, arrearsAmount: st.arrearsAmount })''', '结算提交')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('Terminations 已更新')
