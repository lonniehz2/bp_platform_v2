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
                             data-testid="fee-price" style="width:100%" /></el-form-item></el-col>
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
          <el-col :span="12"><el-form-item label="规则编码" required>
            <el-input v-model="r.ruleCode" placeholder="如 RENT-STD-2026" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则名称" required>
            <el-input v-model="r.ruleName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计费项目ID" required>
            <el-input v-model="r.feeItemId" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="规则类型" required>
            <el-select v-model="r.ruleType" style="width:100%">
              <el-option label="标准价 STANDARD" value="STANDARD" />
              <el-option label="阶梯价 TIERED" value="TIERED" />
              <el-option label="折扣 DISCOUNT" value="DISCOUNT" />
              <el-option label="减免 EXEMPT" value="EXEMPT" />
            </el-select></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="价格配置" required>
            <div style="width:100%">
              <div v-for="(row, i) in kvRows" :key="i"
                   style="display:flex;gap:8px;margin-bottom:6px;align-items:center">
                <el-input v-model="row.k" placeholder="键，如 price / tiers"
                          style="width:200px" :data-testid="'kv-k-' + i" />
                <el-input v-model="row.v" placeholder="值：数字，或 JSON（对象/数组）"
                          style="flex:1" :data-testid="'kv-v-' + i" />
                <el-button link type="danger" @click="kvRows.splice(i, 1)">删除</el-button>
              </div>
              <el-button size="small" @click="kvRows.push({ k: '', v: '' })"
                         data-testid="kv-add">新增一项</el-button>
              <div style="font-size:12px;color:#8c8c8c;margin-top:6px">
                提交时自动组装为 JSON（数字自动识别，其余按字符串/JSON 解析）
              </div>
            </div>
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="生效日期">
            <el-date-picker v-model="r.effectiveStart" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="失效日期">
            <el-date-picker v-model="r.effectiveEnd" type="date"
                            value-format="YYYY-MM-DD" style="width:100%" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="组织ID">
            <el-input v-model="r.orgId" /></el-form-item></el-col>
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
        <el-input v-model="rf.feeItemId" placeholder="计费项目 ID" clearable style="width:210px"
                  data-testid="rule-feeitem" @keyup.enter="loadRules" />
        <el-input v-model="rf.houseType" placeholder="房源类型，如 PUBLIC_RENTAL" clearable
                  style="width:230px" data-testid="rule-housetype" @keyup.enter="loadRules" />
        <el-button type="primary" @click="loadRules" data-testid="rule-search">查询</el-button>
        <el-button @click="resetRuleQuery" data-testid="rule-reset">清空</el-button>
      </div>
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
import { enumLabel } from '@/constants/enums'
import FilterBar from '@/components/FilterBar.vue'

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

function openRule() { ruleCreateVisible.value = true }

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
  r.priceConfig = kvToJson()
  if (!r.ruleCode || !r.ruleName || !r.feeItemId || !r.priceConfig) {
    ElMessage.warning('规则编码、名称、计费项目、价格配置为必填'); return
  }
  try { JSON.parse(r.priceConfig) } catch (e) {
    ElMessage.error('价格配置必须是合法 JSON'); return
  }
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
      `计费项目：${current.value.itemName}\n计费方式：${enumLabel('calcMode', current.value.calcMode)}\n`
      + `试算金额：${money(res?.amount ?? res)}`, '试算结果')
  } finally { saving.value = false }
}

onMounted(() => { load(); loadRules() })
</script>
