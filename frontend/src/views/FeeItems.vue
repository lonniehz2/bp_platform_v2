<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">计费项目</h3>
      <el-tag size="small" type="info">7 种计费方式 · 规则+试算</el-tag>
      <div class="spacer" />
      <el-button type="success" @click="openCreate">新增项目</el-button>
      <el-button @click="openRule">新增计费规则</el-button>
      <el-button @click="ruleVisible = true; loadRules()">规则列表</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
              title="水费 / 电费 / 燃气费单价在此维护：新增项目时「计费方式」选「按表（METER）」，
                     填写「单价」与「计量单位」（度/吨/方），再到「抄表管理」录读数即可出账。" />

    <FilterBar @search="resetAndLoad" @reset="resetQuery">
      <el-input v-model="ff.keyword" placeholder="项目编码 / 名称" clearable
                style="width:200px" data-testid="fee-keyword"
                @keyup.enter="resetAndLoad" />
      <template #more>
        <el-input v-model="ff.itemType" placeholder="项目类型 如 RENT" clearable style="width:170px" />
        <el-input v-model="ff.calcMode" placeholder="计费方式 如 BY_AREA" clearable style="width:190px" />
      </template>
    </FilterBar>

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
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
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
            <el-input v-model="f.itemCode" data-testid="fee-code" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="项目名称" required>
            <el-input v-model="f.itemName" data-testid="fee-name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="费用类型" required>
            <div style="display:flex;gap:6px;width:100%">
              <el-select v-model="f.itemType" style="flex:1">
                <el-option v-for="t in feeTypes" :key="t.typeCode"
                           :label="t.typeName" :value="t.typeCode" />
              </el-select>
              <el-button @click="openFeeTypes">管理</el-button>
            </div></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计费方式" required>
            <el-select v-model="f.calcMode" style="width:100%">
              <el-option label="定额" value="FIXED" />
              <el-option label="按面积" value="BY_AREA" />
              <el-option label="按套" value="BY_HOUSE" />
              <el-option label="按人" value="BY_PERSON" />
              <el-option label="按床位" value="BY_BED" />
              <el-option label="按房晚" value="BY_NIGHT" />
              <el-option label="抄表" value="METER" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="单价" required>
            <el-input-number v-model="f.unitPrice" :min="0" :precision="2"
                             data-testid="fee-price" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计量单位">
            <el-select v-model="f.unit" filterable allow-create default-first-option
                       placeholder="选择或输入" style="width:100%">
              <el-option v-for="u in UNIT_OPTIONS" :key="u" :label="u" :value="u" />
            </el-select></el-form-item></el-col>
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
          <el-col :span="12"><el-form-item label="规则编码" required>
            <el-input v-model="r.ruleCode" placeholder="如 RENT-STD-2026" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则名称" required>
            <el-input v-model="r.ruleName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计费项目" required>
            <el-select v-model="r.feeItemId" filterable style="width:100%">
              <el-option v-for="it in rows" :key="it.id"
                         :label="it.itemName + '（' + it.itemCode + '）'" :value="it.id" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则类型" required>
            <el-select v-model="r.ruleType" style="width:100%">
              <el-option label="标准价" value="STANDARD" />
              <el-option label="阶梯价" value="TIERED" />
              <el-option label="折扣" value="DISCOUNT" />
              <el-option label="减免" value="EXEMPT" />
            </el-select></el-form-item></el-col>
          <el-col :span="24">
            <el-form-item label="价格配置" required>
              <!-- 标准价：单价 -->
              <div v-if="r.ruleType === 'STANDARD'" style="width:100%;display:flex;gap:8px">
                <el-input-number v-model="priceValue" :min="0" :precision="2"
                                 style="flex:1" />
                <span class="muted" style="line-height:32px">元（按项目计量单位）</span>
              </div>
              <!-- 阶梯价：区间上限 + 单价 -->
              <div v-else-if="r.ruleType === 'TIERED'" style="width:100%">
                <div v-for="(t, i) in tiers" :key="i"
                     style="display:flex;gap:8px;margin-bottom:6px;align-items:center">
                  <el-input-number v-model="t.upTo" :min="0" :precision="2"
                                   placeholder="用量上限" style="width:170px" />
                  <el-input-number v-model="t.price" :min="0" :precision="2"
                                   placeholder="单价" style="width:170px" />
                  <el-button link type="danger" @click="tiers.splice(i, 1)">删除</el-button>
                </div>
                <el-button size="small" @click="tiers.push({ upTo: null, price: null })">
                  新增一档
                </el-button>
              </div>
              <!-- 折扣：折扣率 -->
              <div v-else-if="r.ruleType === 'DISCOUNT'" style="width:100%;display:flex;gap:8px">
                <el-input-number v-model="discountRatio" :min="0" :max="1" :step="0.05"
                                 :precision="2" style="flex:1" />
                <span class="muted" style="line-height:32px">0~1，如 0.8 表示 8 折</span>
              </div>
              <!-- 减免 -->
              <div v-else style="width:100%">
                <el-tag type="success">全额减免，无需配置价格</el-tag>
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="12"><el-form-item label="生效日期">
            <el-date-picker v-model="r.effectiveStart" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="失效日期">
            <el-date-picker v-model="r.effectiveEnd" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="适用组织">
            <el-select v-model="r.orgId" filterable clearable style="width:100%"
                       placeholder="留空=全租户通用">
              <el-option v-for="o in orgs" :key="o.id"
                         :label="o.orgName" :value="o.id" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="优先级">
            <el-input-number v-model="r.priority" :min="1" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="适用保障类型">
            <el-select v-model="r.securityType" clearable style="width:100%">
              <el-option label="公租房" value="PUBLIC" />
              <el-option label="保租房" value="AFFORDABLE" />
              <el-option label="人才房" value="TALENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="适用收入档位">
            <el-select v-model="r.incomeLevel" clearable style="width:100%">
              <el-option label="低保 LOW" value="LOW" />
              <el-option label="低收入 LOW_INCOME" value="LOW_INCOME" />
              <el-option label="中低收入 MIDDLE_LOW" value="MIDDLE_LOW" />
              <el-option label="普通 NORMAL" value="NORMAL" />
            </el-select></el-form-item></el-col>
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
      <div class="toolbar" style="margin-bottom:8px">
        <FeeItemSelect v-model="rf.feeItemId" width="210px" testid="feeitemselect" />
        <el-input v-model="rf.houseType" placeholder="房源类型，如 PUBLIC_RENTAL" clearable
                  style="width:230px" data-testid="rule-housetype" @keyup.enter="loadRules" />
        <el-button type="primary" @click="loadRules" data-testid="rule-search">查询</el-button>
        <el-button @click="resetRuleQuery" data-testid="rule-reset">清空</el-button>
        <el-button type="success" @click="openRuleFromList">新增规则</el-button>
      </div>
      <el-table :data="rules" border size="small" max-height="420">
        <el-table-column prop="ruleCode" label="规则编码" width="140" />
        <el-table-column prop="ruleName" label="规则名称" min-width="130" />
        <el-table-column label="计费项目" width="150">
          <template #default="{ row }">{{ itemNameOf(row.feeItemId) }}</template>
        </el-table-column>
        <el-table-column label="价格配置" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ priceText(row.priceConfig) }}</template>
        </el-table-column>
        <el-table-column prop="effectiveStart" label="生效" width="110" />
        <el-table-column label="审批" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.approveStatus === 'APPROVED' ? 'success'
              : (row.approveStatus === 'PENDING' ? 'warning' : 'info')">
              {{ approveText(row.approveStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.approveStatus === 'APPROVED'"
                       @click="editRule(row)">编辑</el-button>
            <el-button link type="danger" :disabled="row.approveStatus === 'APPROVED'"
                       @click="removeRule(row)">删除</el-button>
            <el-button link type="success" :disabled="row.approveStatus === 'APPROVED'"
                       @click="approveRule(row)">审批</el-button>
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


    <!-- 费用类型管理 -->
    <el-dialog v-model="feeTypeVisible" title="费用类型管理" width="560px">
      <div class="toolbar" style="margin-bottom:10px">
        <el-input v-model="ftForm.typeCode" placeholder="编码，如 WATER" style="width:150px" />
        <el-input v-model="ftForm.typeName" placeholder="名称，如 水费" style="width:180px" />
        <el-button type="success" @click="saveFeeType">
          {{ ftForm.id ? '保存修改' : '新增' }}
        </el-button>
        <el-button v-if="ftForm.id" @click="resetFeeTypeForm">取消编辑</el-button>
      </div>
      <el-table :data="feeTypes" border size="small" max-height="360">
        <el-table-column prop="typeCode" label="编码" width="150" />
        <el-table-column prop="typeName" label="名称" min-width="140" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
              {{ row.status === 'ENABLED' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="editFeeType(row)">编辑</el-button>
            <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                       @click="toggleFeeType(row)">
              {{ row.status === 'ENABLED' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-alert type="info" :closable="false" show-icon style="margin-top:10px"
                title="停用后新增计费项目时不再出现在下拉里，历史项目不受影响。" />
    </el-dialog>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
/** 通用详情弹窗（复用 DetailView） */
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import { ref, reactive, onMounted } from 'vue'
import DetailView from '@/components/DetailView.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import FeeItemSelect from '@/components/FeeItemSelect.vue'
import { enumLabel } from '@/constants/enums'
import FilterBar from '@/components/FilterBar.vue'
import { useAuthStore } from '@/store/auth'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
/** 列表筛选条件（后端 /fin/fee-items 支持 keyword / itemType / calcMode）
 *  命名为 ff 以避开创建表单对象 f */
const ff = reactive({ keyword: '', itemType: '', calcMode: '' })
const rules = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const createVisible = ref(false)
const ruleCreateVisible = ref(false)
const ruleVisible = ref(false)
/** 规则列表筛选（后端 /fin/billing-rules 支持 feeItemId / houseType） */
const rf = reactive({ feeItemId: '', houseType: '' })
function resetRuleQuery() {
  rf.feeItemId = ''
  rf.houseType = ''
  loadRules()
}
const previewVisible = ref(false)
const current = ref(null)

const f = reactive({ itemCode: '', itemName: '', itemType: 'RENT',
  calcMode: 'BY_AREA', unitPrice: null, unit: '元/㎡·月', securityType: '' })
const r = reactive({ ruleCode: '', ruleName: '', feeItemId: null,
  ruleType: 'STANDARD', priceConfig: '{"price": 150.00}',
  effectiveStart: '', effectiveEnd: '', orgId: null, priority: 1,
  securityType: '', incomeLevel: '' })
const cp = reactive({ area: 60, quantity: 2, nights: 0 })

function money(v) {
  const n = Number(v)
  return Number.isFinite(n) ? '¥ ' + n.toFixed(2) : '-'
}

async function load() {
  loading.value = true
  try {
    const d = await req.get('/fin/fee-items', {
      params: {
        pageNum: pageNum.value, pageSize: pageSize.value,
        keyword: ff.keyword || undefined,
        itemType: ff.itemType || undefined,
        calcMode: ff.calcMode || undefined
      }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } finally { loading.value = false }
}

/** 查询：回到第 1 页再拉 */
function resetAndLoad() {
  pageNum.value = 1
  load()
}

/** 清空全部筛选条件 */
function resetQuery() {
  ff.keyword = ''
  ff.itemType = ''
  ff.calcMode = ''
  resetAndLoad()
}

async function loadRules() {
  const d = await req.get('/fin/billing-rules', {
    params: {
      pageNum: 1, pageSize: 50,
      feeItemId: rf.feeItemId || undefined,
      houseType: rf.houseType || undefined
    }
  })
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

function openRule() {
  resetRuleForm()
  ruleVisible.value = false
  ruleCreateVisible.value = true
}

/** 价格配置键值行 → JSON 字符串（数字优先，其次 JSON，最后字符串） */
const kvRows = ref([{ k: 'price', v: '150.00' }])
function kvToJson() {
  const obj = {}
  for (const row of kvRows.value) {
    const k = (row.k || '').trim()
    if (!k) continue
    const raw = String(row.v ?? '').trim()
    if (raw === '') { obj[k] = null; continue }
    if (/^-?\d+(\.\d+)?$/.test(raw)) { obj[k] = Number(raw); continue }
    try { obj[k] = JSON.parse(raw) } catch (e) { obj[k] = raw }
  }
  return JSON.stringify(obj)
}

async function doCreateRule() {
  if (!r.ruleCode || !r.ruleName || !r.feeItemId) {
    ElMessage.warning('规则编码、名称、计费项目为必填'); return
  }
  r.priceConfig = buildPriceConfig()
  if (r.ruleType === 'STANDARD' && (priceValue.value === null || priceValue.value === undefined)) {
    ElMessage.warning('请填写标准价单价'); return
  }
  if (r.ruleType === 'DISCOUNT' && (discountRatio.value === null || discountRatio.value === undefined)) {
    ElMessage.warning('请填写折扣比例'); return
  }
  saving.value = true
  try {
    if (r.id) {
      await req.put(`/fin/billing-rules/${r.id}`, { ...r })
      ElMessage.success('规则已保存')
    } else {
      await req.post('/fin/billing-rules', { ...r })
      ElMessage.success('规则已创建（租金类需审批）')
    }
    ruleCreateVisible.value = false
    resetRuleForm()
    loadRules()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
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
      `计费项目：${current.value.itemName}\n计费方式：${enumLabel('calcMode', current.value.calcMode)}\n`
      + `试算金额：${money(res?.amount ?? res)}`, '试算结果')
  } finally { saving.value = false }
}

onMounted(() => { load(); loadRules(); loadFeeTypes(); loadOrgs() })

// ---------------- 费用类型字典 ----------------
const feeTypes = ref([])
const feeTypeVisible = ref(false)
const ftForm = reactive({ id: null, typeCode: '', typeName: '', sortNo: 100 })

async function loadFeeTypes() {
  try {
    feeTypes.value = (await req.get('/fin/fee-types', { params: { enabledOnly: true } })) || []
  } catch (e) { feeTypes.value = [] }
}

function openFeeTypes() {
  resetFeeTypeForm()
  feeTypeVisible.value = true
  loadFeeTypes()
}

function resetFeeTypeForm() {
  Object.assign(ftForm, { id: null, typeCode: '', typeName: '', sortNo: 100 })
}

function editFeeType(row) {
  Object.assign(ftForm, { id: row.id, typeCode: row.typeCode, typeName: row.typeName,
    sortNo: row.sortNo || 100 })
}

async function saveFeeType() {
  if (!ftForm.typeCode || !ftForm.typeName) {
    ElMessage.warning('编码与名称为必填'); return
  }
  if (ftForm.id) {
    await req.put(`/fin/fee-types/${ftForm.id}`, { ...ftForm })
    ElMessage.success('已保存')
  } else {
    await req.post('/fin/fee-types', { ...ftForm })
    ElMessage.success('已新增')
  }
  resetFeeTypeForm()
  loadFeeTypes()
}

async function toggleFeeType(row) {
  const enabled = row.status !== 'ENABLED'
  await req.post(`/fin/fee-types/${row.id}/status`, { enabled })
  ElMessage.success('已更新')
  loadFeeTypes()
}

// ---------------- 单位 ----------------
const UNIT_OPTIONS = ['元/㎡·月', '元/月', '元/吨', '元/度', '元/方', '元/人·月',
  '元/床位·月', '元/晚', '元/次', '元/个·月', '%']

// ---------------- 规则：项目下拉 / 价格配置 / 组织 ----------------
const orgs = ref([])
const priceValue = ref(null)
const discountRatio = ref(null)
const tiers = ref([])

const APPROVE_TEXT = { PENDING: '待审批', APPROVED: '已通过', REJECTED: '已驳回' }
function approveText(s) { return APPROVE_TEXT[s] || s || '—' }
function itemNameOf(id) {
  const it = rows.value.find((x) => String(x.id) === String(id))
  return it ? it.itemName : (id || '—')
}
function priceText(cfg) {
  if (!cfg) return '—'
  try {
    const o = JSON.parse(cfg)
    if (o.price !== undefined) return '单价 ' + o.price
    if (o.ratio !== undefined) return '比例 ' + o.ratio
    if (Array.isArray(o.tiers)) return '阶梯 ' + o.tiers.length + ' 档'
    if (o.exempt) return '全额减免'
    return JSON.stringify(o)
  } catch (e) { return cfg }
}

async function loadOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    orgs.value = d.rows || []
  } catch (e) { orgs.value = [] }
}

/** 默认组织：当前用户所属组织；没有则取第一个 */
function defaultOrgId() {
  const auth = useAuthStore()
  if (auth.user && auth.user.orgId) return auth.user.orgId
  return orgs.value.length ? orgs.value[0].id : null
}

function buildPriceConfig() {
  if (r.ruleType === 'STANDARD') return JSON.stringify({ price: priceValue.value })
  if (r.ruleType === 'TIERED') {
    return JSON.stringify({ tiers: tiers.value.filter((t) => t.upTo !== null && t.price !== null) })
  }
  if (r.ruleType === 'DISCOUNT') return JSON.stringify({ ratio: discountRatio.value })
  return JSON.stringify({ exempt: true })
}

function resetRuleForm() {
  Object.assign(r, { id: null, ruleCode: '', ruleName: '', feeItemId: null,
    ruleType: 'STANDARD', effectiveStart: '', effectiveEnd: '',
    orgId: defaultOrgId(), priority: 10, securityType: '', incomeLevel: '' })
  priceValue.value = null
  discountRatio.value = null
  tiers.value = [{ upTo: null, price: null }]
}

function openRuleFromList() {
  resetRuleForm()
  ruleVisible.value = false
  ruleCreateVisible.value = true
}

function editRule(row) {
  resetRuleForm()
  Object.assign(r, { id: row.id, ruleCode: row.ruleCode, ruleName: row.ruleName,
    feeItemId: row.feeItemId, ruleType: row.ruleType || 'STANDARD',
    effectiveStart: row.effectiveStart || '', effectiveEnd: row.effectiveEnd || '',
    orgId: row.orgId || defaultOrgId(), priority: row.priority || 10,
    securityType: row.securityType || '', incomeLevel: row.incomeLevel || '' })
  try {
    const o = JSON.parse(row.priceConfig || '{}')
    if (o.price !== undefined) priceValue.value = o.price
    if (o.ratio !== undefined) discountRatio.value = o.ratio
    if (Array.isArray(o.tiers) && o.tiers.length) tiers.value = o.tiers
  } catch (e) { /* 忽略 */ }
  ruleVisible.value = false
  ruleCreateVisible.value = true
}

async function removeRule(row) {
  await ElMessageBox.confirm(`确认删除规则「${row.ruleName}」？`, '删除', { type: 'warning' })
  await req.delete(`/fin/billing-rules/${row.id}`)
  ElMessage.success('已删除')
  loadRules()
}
</script>
