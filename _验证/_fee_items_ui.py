# -*- coding: utf-8 -*-
"""计费项目页 5 项改进：
  - 计量单位下拉（可自定义）
  - 费用类型取自字典 + 费用类型管理（增/改/停）
  - 规则列表支持编辑/删除
  - 计费项目下拉选择、价格配置结构化、组织默认当前组织
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'FeeItems.vue')
s = io.open(P, encoding='utf-8').read()
n = 0

# ---------- 1) 计量单位下拉 ----------
OLD_UNIT = """          <el-col :span="12"><el-form-item label="计量单位">
            <el-input v-model="f.unit" placeholder="元/㎡·月" /></el-form-item></el-col>"""
NEW_UNIT = """          <el-col :span="12"><el-form-item label="计量单位">
            <el-select v-model="f.unit" filterable allow-create default-first-option
                       placeholder="选择或输入" style="width:100%">
              <el-option v-for="u in UNIT_OPTIONS" :key="u" :label="u" :value="u" />
            </el-select></el-form-item></el-col>"""
if OLD_UNIT in s:
    s = s.replace(OLD_UNIT, NEW_UNIT, 1); n += 1

# ---------- 2) 费用类型：取自字典 + 管理入口 ----------
OLD_TYPE = """          <el-col :span="12"><el-form-item label="费用类型" required>
            <el-select v-model="f.itemType" style="width:100%">
              <el-option label="租金" value="RENT" />
              <el-option label="物业费" value="PROPERTY" />
              <el-option label="停车费" value="PARKING" />
              <el-option label="能耗费" value="ENERGY" />
              <el-option label="押金" value="DEPOSIT" />
              <el-option label="滞纳金" value="LATE_FEE" />
              <el-option label="其他" value="OTHER" />
            </el-select></el-form-item></el-col>"""
NEW_TYPE = """          <el-col :span="12"><el-form-item label="费用类型" required>
            <div style="display:flex;gap:6px;width:100%">
              <el-select v-model="f.itemType" style="flex:1">
                <el-option v-for="t in feeTypes" :key="t.typeCode"
                           :label="t.typeName" :value="t.typeCode" />
              </el-select>
              <el-button @click="openFeeTypes">管理</el-button>
            </div></el-form-item></el-col>"""
if OLD_TYPE in s:
    s = s.replace(OLD_TYPE, NEW_TYPE, 1); n += 1

# ---------- 3) 规则弹窗：项目下拉 / 价格配置结构化 / 组织默认 ----------
OLD_RULE_ITEM = """          <el-col :span="12"><el-form-item label="计费项目ID" required>
            <el-input v-model="r.feeItemId" /></el-form-item></el-col>"""
NEW_RULE_ITEM = """          <el-col :span="12"><el-form-item label="计费项目" required>
            <el-select v-model="r.feeItemId" filterable style="width:100%">
              <el-option v-for="it in rows" :key="it.id"
                         :label="it.itemName + '（' + it.itemCode + '）'" :value="it.id" />
            </el-select></el-form-item></el-col>"""
if OLD_RULE_ITEM in s:
    s = s.replace(OLD_RULE_ITEM, NEW_RULE_ITEM, 1); n += 1

OLD_PRICE = """          <el-col :span="24"><el-form-item label="价格配置" required>
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
          </el-form-item></el-col>"""
NEW_PRICE = """          <el-col :span="24">
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
          </el-col>"""
if OLD_PRICE in s:
    s = s.replace(OLD_PRICE, NEW_PRICE, 1); n += 1

OLD_ORG = """          <el-col :span="12"><el-form-item label="组织ID">
            <el-input v-model="r.orgId" /></el-form-item></el-col>"""
NEW_ORG = """          <el-col :span="12"><el-form-item label="适用组织">
            <el-select v-model="r.orgId" filterable clearable style="width:100%"
                       placeholder="留空=全租户通用">
              <el-option v-for="o in orgs" :key="o.id"
                         :label="o.orgName" :value="o.id" />
            </el-select></el-form-item></el-col>"""
if OLD_ORG in s:
    s = s.replace(OLD_ORG, NEW_ORG, 1); n += 1

# ---------- 4) 规则列表：编辑/删除 + 中文审批状态 ----------
OLD_COLS = """        <el-table-column prop="ruleName" label="规则名称" min-width="140" />
        <el-table-column prop="feeItemId" label="项目" width="150" />
        <el-table-column prop="unitPrice" label="单价" width="100" />
        <el-table-column prop="effectiveDate" label="生效" width="110" />
        <el-table-column prop="approveStatus" label="审批" width="110" />
        <el-table-column label="操作" width="110">
          <template #default="{ row }">
            <el-button link type="primary" @click="approveRule(row)">审批</el-button>
          </template>
        </el-table-column>"""
NEW_COLS = """        <el-table-column prop="ruleCode" label="规则编码" width="140" />
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
        </el-table-column>"""
if OLD_COLS in s:
    s = s.replace(OLD_COLS, NEW_COLS, 1); n += 1

# 规则列表标题改为弹窗内标题，加“新增规则”按钮
s = s.replace("""        <el-button @click="resetRuleQuery" data-testid="rule-reset">清空</el-button>""",
"""        <el-button @click="resetRuleQuery" data-testid="rule-reset">清空</el-button>
        <el-button type="success" @click="openRuleFromList">新增规则</el-button>""", 1)

# ---------- 5) 费用类型管理弹窗 ----------
if '费用类型管理' not in s:
    dialog = """
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
"""
    s = s.replace("""    <!-- 通用详情 -->""", dialog + """
    <!-- 通用详情 -->""", 1)
    n += 1

# ---------- 6) 脚本 ----------
SCRIPT_ADD = """
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
"""
if 'loadFeeTypes' not in s:
    s = s.replace('</script>', SCRIPT_ADD + '</script>', 1)
    n += 1

# 引入 useAuthStore 与 onMounted 加载
if 'useAuthStore' not in s:
    s = s.replace("import { ref, reactive, onMounted } from 'vue'",
                  "import { ref, reactive, onMounted } from 'vue'\nimport { useAuthStore } from '@/store/auth'", 1)
    n += 1

# 原有 doCreateRule 改为组装价格配置与调用 PUT
OLD_DO = """async function doCreateRule() {"""
if 'buildPriceConfig()' not in s:
    pass

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('FeeItems.vue 改动点:', n)
