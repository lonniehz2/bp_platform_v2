<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('alert.title') }}</h3>
      <div class="spacer" />
      <el-input v-model="keyword" :placeholder="t('alert.keyword')" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">{{ t('alert.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('alert.reset') }}</el-button>
      <el-button @click="loadStats">{{ t('alert.stats') }}</el-button>
      <el-button type="success" @click="createVisible = true">{{ t('alert.create') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon :title="t('alert.tip')"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('alert.empty')">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="alertType" :label="t('alert.type')" width="150">
        <template #default="{ row }">{{ enumLabel('alertType', row.alertType) || row.alertTypeLabel }}</template>
      </el-table-column>
      <el-table-column prop="alertLevel" :label="t('alert.level')" width="100">
        <template #default="{ row }">{{ enumLabel('alertLevel', row.alertLevel) || row.alertLevelLabel }}</template>
      </el-table-column>
      <el-table-column prop="alertStatus" :label="t('alert.status')" width="110">
        <template #default="{ row }">{{ enumLabel('alertStatus', row.alertStatus) || row.alertStatusLabel }}</template>
      </el-table-column>
      <el-table-column prop="alertContent" :label="t('alert.content')" width="200" />
      <el-table-column :label="t('alert.actions')" width="210" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('alert.detail') }}</el-button>
          <el-button link type="warning" @click="actAction(row, '/alerts/{id}/handle', t('alert.handle'))">{{ t('alert.handle') }}</el-button>
          <el-dropdown trigger="click" style="margin-left:8px">
            <el-button link type="primary">{{ t('alert.more') }}</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="actAction(row, '/alerts/{id}/resolve', '解决')">{{ t('alert.resolve') }}</el-dropdown-item>
                <el-dropdown-item @click="actAction(row, '/alerts/{id}/ignore', '忽略')">{{ t('alert.ignore') }}</el-dropdown-item>
                <el-dropdown-item @click="actAction(row, '/alerts/{id}/escalate', '升级')">{{ t('alert.escalate') }}</el-dropdown-item>
                <el-dropdown-item @click="actAction(row, '/alerts/{id}/to-workorder', '转工单')">{{ t('alert.toWorkOrder') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <!-- ==================== 规则引擎 ==================== -->
    <div class="page-card">
      <div class="toolbar">
        <h4 style="margin:0">{{ t('alert.rulesetTitle') }}</h4>
        <el-tag size="small" type="info">{{ t('alert.rulesetHint') }}</el-tag>
        <div class="spacer" />
        <el-select v-model="rsDomain" :placeholder="t('alert.domain')" clearable style="width:130px"
                   @change="loadRulesets">
          <el-option :label="t('alert.alertDomain')" value="ALERT" />
          <el-option :label="t('alert.billing')" value="BILLING" />
          <el-option :label="t('alert.credit')" value="CREDIT" />
        </el-select>
        <el-select v-model="rsStatus" :placeholder="t('alert.status')" clearable style="width:120px"
                   @change="loadRulesets">
          <el-option :label="t('alert.draft')" value="DRAFT" />
          <el-option :label="t('alert.published')" value="PUBLISHED" />
          <el-option :label="t('alert.disabled')" value="DISABLED" />
        </el-select>
        <el-button @click="loadRulesets">{{ t('alert.refresh') }}</el-button>
        <el-button type="success" @click="openRuleset">{{ t('alert.newRuleset') }}</el-button>
      </div>

      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="层级关系：先建「规则集」（可理解为某一场景的规则包），再在其中加「规则」（单条阈值判定）；规则集发布后生效，旧版本自动停用。" />
      <el-table :data="rulesets" v-loading="rsLoading" border size="small"
                highlight-current-row :current-row-key="currentRuleset?.id"
                row-key="id" @current-change="onPickRuleset">
        <el-table-column prop="rulesetCode" :label="t('alert.code')" width="170" />
        <el-table-column prop="rulesetName" :label="t('alert.name')" min-width="160" />
        <el-table-column :label="t('alert.domain')" width="100">
          <template #default="{ row }">{{ domainText(row.domain) }}</template>
        </el-table-column>
        <el-table-column :label="t('alert.scenario')" width="130">
          <template #default="{ row }">{{ scenarioText(row.scenario) }}</template>
        </el-table-column>
        <el-table-column prop="rulesetVersion" :label="t('alert.version')" width="80" />
        <el-table-column prop="rulesetStatus" :label="t('alert.statusCol')" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.rulesetStatus === 'PUBLISHED' ? 'success'
              : (row.rulesetStatus === 'DISABLED' ? 'info' : 'warning')">
              {{ enumLabel('rulesetStatus', row.rulesetStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('alert.actions')" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewRules(row)">{{ t('alert.viewRules') }}</el-button>
            <el-button link type="success" :disabled="row.rulesetStatus === 'PUBLISHED'"
                       @click="publishRuleset(row)">{{ t('alert.publish') }}</el-button>
            <el-button link type="warning" :disabled="row.rulesetStatus === 'DISABLED'"
                       @click="disableRuleset(row)">{{ t('alert.disable') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="currentRuleset" style="margin-top:14px">
        <div class="toolbar" style="margin-bottom:8px">
          <h4 style="margin:0">
            规则明细：{{ currentRuleset.rulesetName }}
            <span class="muted" style="font-size:12px">（v{{ currentRuleset.rulesetVersion }}）</span>
          </h4>
          <div class="spacer" />
          <el-button type="success" size="small"
                     :disabled="currentRuleset.rulesetStatus === 'PUBLISHED'"
                     @click="openRule">{{ t('alert.addRule') }}</el-button>
        </div>
        <el-table :data="rules" border size="small">
          <el-table-column prop="ruleCode" :label="t('alert.code')" width="150" />
          <el-table-column prop="ruleName" :label="t('alert.name')" min-width="140" />
          <el-table-column :label="t('alert.condition')" min-width="190" show-overflow-tooltip>
            <template #default="{ row }">{{ humanCondition(row.conditionExpr) }}</template>
          </el-table-column>
          <el-table-column :label="t('alert.threshold')" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ humanThreshold(row.thresholdJson) }}</template>
          </el-table-column>
          <el-table-column prop="severity" :label="t('alert.level')" width="90">
            <template #default="{ row }">{{ enumLabel('alertLevel', row.severity) }}</template>
          </el-table-column>
          <el-table-column prop="priority" :label="t('alert.priority')" width="90" />
          <el-table-column prop="ruleStatus" :label="t('alert.statusCol')" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.ruleStatus === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('ruleStatus', row.ruleStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('alert.actions')" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRule(row)">{{ t('alert.edit') }}</el-button>
              <el-button link :type="row.ruleStatus === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleRule(row)">
                {{ row.ruleStatus === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!rules.length" class="muted" style="margin-top:8px">{{ t('alert.noRules') }}</div>
      </div>
    </div>

    <!-- 新建规则集 -->
    <el-dialog v-model="rulesetVisible" :title="t('alert.createTitle')" width="560px">
      <el-form :model="rs" label-width="110px">
        <el-form-item :label="t('alert.code')" required>
          <el-input v-model="rs.code" :placeholder="t('alert.codeHint')" />
        </el-form-item>
        <el-form-item :label="t('alert.name')" required>
          <el-input v-model="rs.name" />
        </el-form-item>
        <el-form-item :label="t('alert.domain')" required>
          <el-select v-model="rs.domain" style="width:100%">
            <el-option label="告警" value="ALERT" />
            <el-option label="计费" value="BILLING" />
            <el-option label="信用" value="CREDIT" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('alert.scenario')">
          <el-input v-model="rs.scenario" :placeholder="t('alert.scenarioHint')" />
        </el-form-item>
        <el-form-item :label="t('alert.description')">
          <el-input v-model="rs.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="同编码再次创建会自动递增版本；新版本为草稿，发布后旧版本自动停用" />
      <template #footer>
        <el-button @click="rulesetVisible = false">{{ t('alert.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateRuleset">{{ t('alert.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑规则 -->
    <el-dialog v-model="ruleVisible" :title="rf2.id ? t('alert.editRule') : t('alert.newRule')" width="620px">
      <el-form :model="rf2" label-width="110px">
        <el-form-item label="规则编码" required>
          <el-input v-model="rf2.code" :placeholder="t('alert.codeHint')" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="rf2.name" :placeholder="t('alert.nameHint')" />
        </el-form-item>
        <el-form-item label="监控字段" required>
          <el-select v-model="rf2.field" style="width:100%">
            <el-option v-for="f in RULE_FIELDS" :key="f.key" :label="f.label" :value="f.key" />
          </el-select>
        </el-form-item>
        <el-form-item label="判定条件" required>
          <div style="display:flex;gap:8px;width:100%">
            <el-select v-model="rf2.op" style="width:110px">
              <el-option label="大于 >" value=">" />
              <el-option label="大于等于 ≥" value=">=" />
              <el-option label="小于 <" value="<" />
              <el-option label="小于等于 ≤" value="<=" />
              <el-option label="等于 =" value="=" />
            </el-select>
            <el-input v-model.number="rf2.value" placeholder="阈值，如 30" />
          </div>
        </el-form-item>
        <el-form-item label="生成条件">
          <el-input :model-value="previewCondition()" readonly />
        </el-form-item>
        <el-form-item label="生成阈值">
          <el-input :model-value="previewThreshold()" readonly />
        </el-form-item>
        <el-form-item label="严重级别">
          <el-select v-model="rf2.severity" style="width:100%">
            <el-option label="提示" value="INFO" />
            <el-option label="警告" value="WARNING" />
            <el-option label="严重" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="动作">
          <el-select v-model="rf2.actionType" style="width:100%">
            <el-option label="仅记录告警" value="" />
            <el-option label="通知组织管理员" value="NOTIFY_ORG" />
            <el-option label="生成工单" value="WORKORDER" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="rf2.priority" :min="1" style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="只需选字段、运算符与阈值；条件表达式与阈值 JSON 会自动生成，无需手写。" />
      <template #footer>
        <el-button @click="ruleVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doAddRule">保存</el-button>
      </template>
    </el-dialog>
    <el-dialog v-model="createVisible" title="新建告警" width="700px">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="字段与后端 AlertCreateCmd 一致；带 * 为必填" />
      <el-form :model="form" label-width="110px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="告警类别" required>
            <el-select v-model="form.alertCategory" style="width:100%" data-testid="f-alertCategory">
              <el-option label="安全隐患" value="SAFETY" />
              <el-option label="设备异常" value="DEVICE" />
              <el-option label="业务风险" value="BUSINESS" />
              <el-option label="违规行为" value="VIOLATION" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="告警级别" required>
            <el-select v-model="form.alertLevel" style="width:100%" data-testid="f-alertLevel">
              <el-option label="紧急" value="URGENT" />
              <el-option label="重要" value="IMPORTANT" />
              <el-option label="普通" value="NORMAL" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="告警类型" required>
            <el-input v-model="form.alertType" data-testid="f-alertType"
                      placeholder="如 ARREAR_RATE / DEVICE_OFFLINE" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="组织 ID">
            <OrgSelect v-model="form.orgId" width="100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="告警标题" required>
            <el-input v-model="form.alertTitle" data-testid="f-alertTitle"
                      placeholder="一句话说明问题，≤255 字符" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="告警内容">
            <el-input v-model="form.alertContent" type="textarea" :rows="3"
                      data-testid="f-alertContent" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="实际值">
            <el-input v-model="form.alertValue" placeholder="如 15%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="阈值">
            <el-input v-model="form.thresholdValue" placeholder="如 10%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="关联房源 ID">
            <HouseSelect v-model="form.houseId" width="100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="关联人员 ID">
            <PersonPicker v-model="form.personId" width="240px" testid="person-picker" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">提交</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView，字段与中文名来自后端字段字典） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import DetailView from '@/components/DetailView.vue'
import JsonForm from '@/components/JsonForm.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { useAuthStore } from '@/store/auth'
import HouseSelect from '@/components/HouseSelect.vue'
import OrgSelect from '@/components/OrgSelect.vue'

const auth = useAuthStore()

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const show = ref(false)
const detail = ref(null)
const createVisible = ref(false)

/** 字段名严格对齐后端 AlertCreateCmd */
const form = reactive({
  alertCategory: 'SAFETY',
  alertType: '',
  alertLevel: 'NORMAL',
  alertTitle: '',
  alertContent: '',
  alertValue: '',
  thresholdValue: '',
  orgId: '',
  houseId: '',
  personId: ''
})

const SCHEMA = [
  { key: 'alertCategory', label: '告警类别', type: 'select', required: true, options: [
    { label: '安全隐患', value: 'SAFETY' }, { label: '设备异常', value: 'DEVICE' },
    { label: '业务风险', value: 'BUSINESS' }, { label: '违规行为', value: 'VIOLATION' }
  ] },
  { key: 'alertLevel', label: '告警级别', type: 'select', required: true, options: [
    { label: '紧急', value: 'URGENT' }, { label: '重要', value: 'IMPORTANT' },
    { label: '普通', value: 'NORMAL' }
  ] },
  { key: 'alertType', label: '告警类型', required: true, placeholder: '如 ARREAR_RATE / DEVICE_OFFLINE，≤40 字符' },
  { key: 'orgId', label: '组织 ID', placeholder: '可空，填真实主键' },
  { key: 'alertTitle', label: '告警标题', required: true, span: 24, placeholder: '一句话说明问题，≤255 字符' },
  { key: 'alertContent', label: '告警内容', type: 'textarea', span: 24, rows: 3 },
  { key: 'alertValue', label: '实际值', placeholder: '如 15%' },
  { key: 'thresholdValue', label: '阈值', placeholder: '如 10%' },
  { key: 'houseId', label: '关联房源 ID' },
  { key: 'personId', label: '关联人员 ID' }
]

async function load() {
  loading.value = true
  try {
    const d = await req.get('/alerts', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value,
                keyword: keyword.value || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function doCreate() {
  // 必填项与 AlertCreateCmd 的 @NotBlank 一致
  const missing = []
  if (!form.alertCategory) missing.push('告警类别')
  if (!form.alertType) missing.push('告警类型')
  if (!form.alertLevel) missing.push('告警级别')
  if (!form.alertTitle) missing.push('告警标题')
  if (missing.length) { ElMessage.warning('请填写：' + missing.join('、')); return }

  saving.value = true
  try {
    await req.post('/alerts', { ...form })
    ElMessage.success('创建成功')
    createVisible.value = false; load()
  } finally { saving.value = false }
}

/** 带原因的动作 */
async function actReason(row, path, label) {
  const { value } = await ElMessageBox.prompt('请输入' + label + '原因', label, {
    inputValue: ''
  })
  await req.post(`${pathTpl(path, row.id)}`, { reason: value })
  ElMessage.success(label + '成功'); load()
}
function pathTpl(p, id) { return p.replace('{id}', id) }

/** 无参数动作 */
async function actPlain(row, path, label) {
  await ElMessageBox.confirm('确认执行「' + label + '」？', label, { type: 'warning' })
  await req.post(pathTpl(path, row.id))
  ElMessage.success(label + '成功'); load()
}

async function actAction(row, path, label) {
  const { value } = await ElMessageBox.prompt('处理结果', label, { inputValue: '' })
  await req.post(pathTpl(path, row.id),
                 { handleUserId: auth.user?.userId, action: label, result: value })
  ElMessage.success(label + '成功'); load()
}
async function loadStats() {
  const r = await req.get('/alerts/stats')
  ElMessageBox.alert(JSON.stringify(r, null, 2).slice(0, 900), '告警统计')
}

function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}

onMounted(load)

// ---------------- 规则引擎 ----------------
const rulesets = ref([])
const rules = ref([])
const currentRuleset = ref(null)
const rsLoading = ref(false)
const rsDomain = ref('')
const rsStatus = ref('')
const rulesetVisible = ref(false)
const ruleVisible = ref(false)
const rs = reactive({ code: '', name: '', domain: 'ALERT', scenario: '', description: '' })

// 规则集的域与场景（后端存英文编码，这里展示中文）
const DOMAIN_LABEL = {
  ALERT: '告警', BILLING: '计费', FINANCE: '财务', CREDIT: '信用',
  IOT: '物联', SECURITY: '安全', CONTRACT: '合同'
}
const SCENARIO_LABEL = {
  ARREAR: '欠费', OVERDUE: '逾期', RENEWAL: '续租', CHECKIN: '入住',
  CHECKOUT: '退租', BILLING: '出账', CREDIT: '信用评估', ALERT: '告警',
  CONTRACT: '合同', PAYMENT: '缴费', X: '默认'
}
function domainText(v) { return DOMAIN_LABEL[v] || v || '—' }
function scenarioText(v) { return SCENARIO_LABEL[v] || v || '—' }

const RULE_FIELDS = [
  { key: 'overdueDays', label: '逾期天数' },
  { key: 'amount', label: '金额（元）' },
  { key: 'count', label: '次数' },
  { key: 'days', label: '天数' },
  { key: 'ratio', label: '比例（0~1）' }
]
const rf2 = reactive({ id: null, code: '', name: '', field: 'overdueDays', op: '>',
  value: 30, severity: 'WARNING', actionType: '', priority: 10 })

function previewCondition() {
  if (!rf2.field || !rf2.op || rf2.value === null || rf2.value === '') return '（请选择字段与阈值）'
  return `${rf2.field} ${rf2.op} ${rf2.value}`
}
function previewThreshold() {
  if (!rf2.field) return '{}'
  return JSON.stringify({ [rf2.field]: rf2.value })
}

const FIELD_LABEL = Object.fromEntries(RULE_FIELDS.map((f) => [f.key, f.label]))
const OP_LABEL = { '>': '大于', '>=': '大于等于', '<': '小于', '<=': '小于等于', '=': '等于' }

/** 条件表达式 → 中文，如「逾期天数 大于 30」 */
function humanCondition(expr) {
  if (!expr) return '—'
  const m = String(expr).match(/^\s*(\w+)\s*(>=|<=|>|<|=)\s*([\d.]+)\s*$/)
  if (!m) return expr
  return `${FIELD_LABEL[m[1]] || m[1]} ${OP_LABEL[m[2]] || m[2]} ${m[3]}`
}

/** 阈值 JSON → 中文键值，如「逾期天数 = 30」 */
function humanThreshold(json) {
  if (!json) return '—'
  try {
    const o = JSON.parse(json)
    return Object.entries(o).map(([k, v]) => `${FIELD_LABEL[k] || k} = ${v}`).join('；')
  } catch (e) {
    return json
  }
}

async function loadRulesets() {
  rsLoading.value = true
  try {
    rulesets.value = await req.get('/rules/rulesets', {
      params: { domain: rsDomain.value || undefined, status: rsStatus.value || undefined }
    }) || []
    // 默认选中第一个，让「规则明细」直接可见，避免用户以为两者无关
    if (!currentRuleset.value && rulesets.value.length) {
      viewRules(rulesets.value[0])
    }
  } catch (e) {
    rulesets.value = []
  } finally { rsLoading.value = false }
}

function onPickRuleset(row) {
  if (row) viewRules(row)
}

async function viewRules(row) {
  currentRuleset.value = row
  try {
    rules.value = await req.get(`/rules/rulesets/${row.id}/rules`) || []
  } catch (e) { rules.value = [] }
}

function openRuleset() {
  Object.assign(rs, { code: '', name: '', domain: 'ALERT', scenario: '', description: '' })
  rulesetVisible.value = true
}

async function doCreateRuleset() {
  if (!rs.code || !rs.name || !rs.domain) {
    ElMessage.warning('编码、名称、域为必填'); return
  }
  saving.value = true
  try {
    await req.post('/rules/rulesets', { ...rs })
    ElMessage.success('规则集已创建（草稿）')
    rulesetVisible.value = false
    loadRulesets()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally { saving.value = false }
}

async function publishRuleset(row) {
  await ElMessageBox.confirm(
    `发布后规则集「${row.rulesetName}」立即生效，同编码旧版本自动停用。确认发布？`,
    '发布规则集', { type: 'warning' })
  await req.post(`/rules/rulesets/${row.id}/publish`)
  ElMessage.success('已发布')
  loadRulesets()
}

async function disableRuleset(row) {
  await ElMessageBox.confirm(`确认停用规则集「${row.rulesetName}」？`, '停用', { type: 'warning' })
  await req.post(`/rules/rulesets/${row.id}/disable`)
  ElMessage.success('已停用')
  loadRulesets()
}

function openRule(row) {
  if (row) {
    // 从已有条件反解字段/运算符/阈值，便于编辑
    const m = String(row.conditionExpr || '').match(/^\s*(\w+)\s*(>=|<=|>|<|=)\s*([\d.]+)/)
    let field = 'overdueDays'
    let value = 30
    try {
      const t = JSON.parse(row.thresholdJson || '{}')
      const k = Object.keys(t)[0]
      if (k) { field = k; value = t[k] }
    } catch (e) { /* 忽略 */ }
    Object.assign(rf2, {
      id: row.id, code: row.ruleCode, name: row.ruleName,
      field, op: m ? m[2] : '>', value: m ? Number(m[3]) : value,
      severity: row.severity || 'WARNING',
      actionType: (row.actionsJson || '').includes('WORKORDER') ? 'WORKORDER'
        : ((row.actionsJson || '').includes('NOTIFY') ? 'NOTIFY_ORG' : ''),
      priority: row.priority || 10
    })
  } else {
    Object.assign(rf2, { id: null, code: '', name: '', field: 'overdueDays', op: '>',
      value: 30, severity: 'WARNING', actionType: '', priority: 10 })
  }
  ruleVisible.value = true
}

async function doAddRule() {
  if (!rf2.code || !rf2.name) {
    ElMessage.warning('规则编码与名称为必填'); return
  }
  if (rf2.value === null || rf2.value === '' || Number.isNaN(Number(rf2.value))) {
    ElMessage.warning('请填写阈值'); return
  }
  const payload = {
    code: rf2.code,
    name: rf2.name,
    conditionExpr: previewCondition(),
    thresholdJson: previewThreshold(),
    severity: rf2.severity,
    actionsJson: rf2.actionType === 'WORKORDER' ? '{"workorder":true}'
      : (rf2.actionType === 'NOTIFY_ORG' ? '{"notify":["org_manager"]}' : ''),
    priority: rf2.priority
  }
  saving.value = true
  try {
    if (rf2.id) {
      await req.put(`/rules/rules/${rf2.id}`, payload)
      ElMessage.success('规则已保存')
    } else {
      await req.post(`/rules/rulesets/${currentRuleset.value.id}/rules`, payload)
      ElMessage.success('规则已新增')
    }
    ruleVisible.value = false
    viewRules(currentRuleset.value)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally { saving.value = false }
}

async function toggleRule(row) {
  const next = row.ruleStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  await req.post(`/rules/rules/${row.id}/status`, { status: next })
  ElMessage.success('已更新')
  viewRules(currentRuleset.value)
}

onMounted(loadRulesets)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>