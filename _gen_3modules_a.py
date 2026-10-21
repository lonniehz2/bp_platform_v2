# -*- coding: utf-8 -*-
"""① 合同同住人 ② 计费项目（含规则/试算）③ 空间新增删除"""
import io
import os

V = r'D:\Work\业务平台开发\frontend\src\views'

# ============ ① 同住人（嵌入合同页的抽屉组件） ============
COHAB = '''<template>
  <div>
    <div class="toolbar">
      <el-tag size="small" type="info">保障人口影响配租面积与补贴额度</el-tag>
      <el-tag size="small">家庭人口：{{ householdSize }}</el-tag>
      <div class="spacer" />
      <el-button type="success" size="small" @click="openCreate">登记同住人</el-button>
      <el-button size="small" @click="loadAll">刷新</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="memberName" label="姓名" width="120" />
      <el-table-column prop="relation" label="关系" width="110">
        <template #default="{ row }">{{ enumLabel('relation', row.relation) }}</template>
      </el-table-column>
      <el-table-column prop="idCardMask" label="证件号(脱敏)" width="180" />
      <el-table-column label="门禁授权" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="Number(row.isGranted) === 1 ? 'success' : 'info'">
            {{ Number(row.isGranted) === 1 ? '已授权' : '未授权' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary"
                     @click="toggleGrant(row)">
            {{ Number(row.isGranted) === 1 ? '取消授权' : '授予门禁' }}
          </el-button>
          <el-button link type="danger" @click="remove(row)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="visible" title="登记同住人" width="520px">
      <el-form :model="f" label-width="110px">
        <el-form-item label="姓名" required>
          <el-input v-model="f.memberName" /></el-form-item>
        <el-form-item label="关联人员ID">
          <el-input v-model.number="f.personId" placeholder="已有人员档案时填写" />
        </el-form-item>
        <el-form-item label="证件号(脱敏)">
          <el-input v-model="f.idCardMask" placeholder="如 3506**********1234" />
        </el-form-item>
        <el-form-item label="与承租人关系">
          <el-select v-model="f.relation" style="width:100%">
            <el-option label="配偶" value="SPOUSE" />
            <el-option label="子女" value="CHILD" />
            <el-option label="父母" value="PARENT" />
            <el-option label="其他亲属" value="RELATIVE" />
            <el-option label="其他" value="OTHER" />
          </el-select></el-form-item>
        <el-form-item label="同步门禁授权">
          <el-switch v-model="f.isGranted" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

const props = defineProps({ contractId: { type: [String, Number], default: null } })

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const householdSize = ref(0)
const visible = ref(false)
const f = reactive({ personId: null, memberName: '', idCardMask: '',
  relation: 'SPOUSE', isGranted: 0 })

async function loadAll() {
  if (!props.contractId) return
  loading.value = true
  try {
    const d = await req.get(`/contracts/${props.contractId}/cohabitants`)
    rows.value = Array.isArray(d) ? d : (d.rows || [])
    const hs = await req.get(
      `/contracts/${props.contractId}/cohabitants/household-size`)
    householdSize.value = typeof hs === 'number' ? hs
      : (hs?.householdSize ?? hs?.size ?? rows.value.length + 1)
  } catch (e) { rows.value = [] } finally { loading.value = false }
}

function openCreate() {
  Object.assign(f, { personId: null, memberName: '', idCardMask: '',
    relation: 'SPOUSE', isGranted: 0 })
  visible.value = true
}

async function doCreate() {
  if (!f.memberName) { ElMessage.warning('请填写同住人姓名'); return }
  saving.value = true
  try {
    await req.post(`/contracts/${props.contractId}/cohabitants`, { ...f })
    ElMessage.success('已登记')
    visible.value = false; loadAll()
  } finally { saving.value = false }
}

async function toggleGrant(row) {
  const granted = Number(row.isGranted) !== 1
  await req.post(
    `/contracts/${props.contractId}/cohabitants/${row.id}/grant`, { granted })
  ElMessage.success(granted ? '已授予门禁' : '已取消授权'); loadAll()
}

async function remove(row) {
  await ElMessageBox.confirm(`确认移除同住人「${row.memberName}」？`, '移除确认',
    { type: 'warning' })
  await req.delete(`/contracts/${props.contractId}/cohabitants/${row.id}`)
  ElMessage.success('已移除'); loadAll()
}

watch(() => props.contractId, loadAll, { immediate: true })
</script>
'''

os.makedirs(os.path.join(V, '..', 'components'), exist_ok=True)
io.open(r'D:\Work\业务平台开发\frontend\src\components\CohabitantPanel.vue',
        'w', encoding='utf-8').write(COHAB)
print('  ✓ components/CohabitantPanel.vue')

# ============ ② 计费项目（含计费规则 + 试算） ============
FEE = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">计费项目</h3>
      <el-tag size="small" type="info">7 种计费方式 · 规则+试算</el-tag>
      <div class="spacer" />
      <el-button type="success" @click="openCreate">新增项目</el-button>
      <el-button @click="openRule">新增计费规则</el-button>
      <el-button @click="ruleVisible = true; loadRules()">规则列表</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="itemCode" label="项目编码" width="150" />
      <el-table-column prop="itemName" label="名称" min-width="140" />
      <el-table-column label="类型" width="110">
        <template #default="{ row }">{{ enumLabel('itemType', row.itemType) }}</template>
      </el-table-column>
      <el-table-column label="计费方式" width="120">
        <template #default="{ row }">{{ row.calcModeLabel || enumLabel('calcMode', row.calcMode) }}</template>
      </el-table-column>
      <el-table-column prop="unitPrice" label="单价" width="110">
        <template #default="{ row }">{{ money(row.unitPrice) }}</template>
      </el-table-column>
      <el-table-column prop="unit" label="单位" width="110" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
            {{ enumLabel('status', row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="toggle(row)">
            {{ row.status === 'ENABLED' ? '停用' : '启用' }}
          </el-button>
          <el-button link @click="preview(row)">试算</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <!-- 新增项目 FeeItemCreateCmd -->
    <el-dialog v-model="createVisible" title="新增计费项目" width="600px">
      <el-form :model="f" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="项目编码" required>
            <el-input v-model="f.itemCode" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="项目名称" required>
            <el-input v-model="f.itemName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="费用类型" required>
            <el-select v-model="f.itemType" style="width:100%">
              <el-option label="租金" value="RENT" />
              <el-option label="物业费" value="PROPERTY" />
              <el-option label="停车费" value="PARKING" />
              <el-option label="能耗费" value="ENERGY" />
              <el-option label="押金" value="DEPOSIT" />
              <el-option label="滞纳金" value="LATE_FEE" />
              <el-option label="其他" value="OTHER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计费方式" required>
            <el-select v-model="f.calcMode" style="width:100%">
              <el-option label="定额 FIXED" value="FIXED" />
              <el-option label="按面积 BY_AREA" value="BY_AREA" />
              <el-option label="按套 BY_HOUSE" value="BY_HOUSE" />
              <el-option label="按人 BY_PERSON" value="BY_PERSON" />
              <el-option label="按床位 BY_BED" value="BY_BED" />
              <el-option label="按房晚 BY_NIGHT" value="BY_NIGHT" />
              <el-option label="抄表 METER" value="METER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="单价" required>
            <el-input-number v-model="f.unitPrice" :min="0" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计量单位">
            <el-input v-model="f.unit" placeholder="元/㎡·月" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="保障类型">
            <el-select v-model="f.securityType" style="width:100%" clearable>
              <el-option label="公租房" value="PUBLIC" />
              <el-option label="保租房" value="AFFORDABLE" />
              <el-option label="人才房" value="TALENT" />
              <el-option label="廉租房" value="LOW_RENT" />
            </el-select></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 计费规则 BillingRuleCreateCmd -->
    <el-dialog v-model="ruleCreateVisible" title="新增计费规则" width="620px">
      <el-form :model="r" label-width="130px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="计费项目ID" required>
            <el-input v-model.number="r.feeItemId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则名称">
            <el-input v-model="r.ruleName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="生效日期">
            <el-date-picker v-model="r.effectiveDate" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="失效日期">
            <el-date-picker v-model="r.expireDate" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则单价">
            <el-input-number v-model="r.unitPrice" :precision="2" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="组织ID">
            <el-input v-model.number="r.orgId" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="规则需审批后生效；未审批时出账使用项目默认单价" />
      <template #footer>
        <el-button @click="ruleCreateVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateRule">保存</el-button>
      </template>
    </el-dialog>

    <!-- 规则列表 -->
    <el-dialog v-model="ruleVisible" title="计费规则" width="720px">
      <el-table :data="rules" border size="small" max-height="420">
        <el-table-column prop="ruleName" label="规则名称" min-width="140" />
        <el-table-column prop="feeItemId" label="项目" width="150" />
        <el-table-column prop="unitPrice" label="单价" width="100" />
        <el-table-column prop="effectiveDate" label="生效" width="110" />
        <el-table-column prop="approveStatus" label="审批" width="110" />
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            <el-button link type="primary" @click="approveRule(row)">审批</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 试算 CalcPreviewCmd -->
    <el-dialog v-model="previewVisible" title="计费试算" width="460px">
      <el-form :model="cp" label-width="120px">
        <el-form-item label="计费项目">
          <el-input :model-value="current?.itemName" disabled /></el-form-item>
        <el-form-item label="面积(㎡)">
          <el-input-number v-model="cp.area" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="数量/人口">
          <el-input-number v-model="cp.quantity" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="天数/房晚">
          <el-input-number v-model="cp.nights" :min="0" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="previewVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doPreview">试算</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const rules = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const createVisible = ref(false)
const ruleCreateVisible = ref(false)
const ruleVisible = ref(false)
const previewVisible = ref(false)
const current = ref(null)

const f = reactive({ itemCode: '', itemName: '', itemType: 'RENT',
  calcMode: 'BY_AREA', unitPrice: null, unit: '元/㎡·月', securityType: '' })
const r = reactive({ feeItemId: null, ruleName: '', effectiveDate: '',
  expireDate: '', unitPrice: null, orgId: null })
const cp = reactive({ area: 60, quantity: 2, nights: 0 })

function money(v) {
  const n = Number(v)
  return Number.isFinite(n) ? '¥ ' + n.toFixed(2) : '-'
}

async function load() {
  loading.value = true
  try {
    const d = await req.get('/fin/fee-items', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } finally { loading.value = false }
}

async function loadRules() {
  const d = await req.get('/fin/billing-rules', { params: { pageNum: 1, pageSize: 50 } })
  rules.value = d.rows || d || []
}

function openCreate() { createVisible.value = true }
async function doCreate() {
  if (!f.itemCode || !f.itemName || !f.unitPrice) {
    ElMessage.warning('编码、名称、单价为必填'); return
  }
  saving.value = true
  try {
    await req.post('/fin/fee-items', { ...f })
    ElMessage.success('项目已创建')
    createVisible.value = false; load()
  } finally { saving.value = false }
}

function openRule() { ruleCreateVisible.value = true }
async function doCreateRule() {
  if (!r.feeItemId) { ElMessage.warning('请填写计费项目ID'); return }
  saving.value = true
  try {
    await req.post('/fin/billing-rules', { ...r })
    ElMessage.success('规则已创建（待审批）')
    ruleCreateVisible.value = false
  } finally { saving.value = false }
}

async function approveRule(row) {
  await ElMessageBox.confirm('确认审批通过该计费规则？', '审批', { type: 'warning' })
  await req.post(`/fin/billing-rules/${row.id}/approve`)
  ElMessage.success('已审批'); loadRules()
}

async function toggle(row) {
  const next = row.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  await req.post(`/fin/fee-items/${row.id}/status`, { status: next })
  ElMessage.success('已' + (next === 'ENABLED' ? '启用' : '停用')); load()
}

function preview(row) {
  current.value = row
  previewVisible.value = true
}
async function doPreview() {
  saving.value = true
  try {
    const res = await req.post('/fin/calc-preview', {
      feeItemId: current.value.id, ...cp
    })
    ElMessageBox.alert(
      `计费项目：${current.value.itemName}\\n计费方式：${enumLabel('calcMode', current.value.calcMode)}\\n`
      + `试算金额：${money(res?.amount ?? res)}`, '试算结果')
  } finally { saving.value = false }
}

onMounted(() => { load(); loadRules() })
</script>
'''

io.open(os.path.join(V, 'FeeItems.vue'), 'w', encoding='utf-8').write(FEE)
print('  ✓ FeeItems.vue 重写（新增/启停/规则/审批/试算）')
