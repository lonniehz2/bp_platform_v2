# -*- coding: utf-8 -*-
"""规则引擎：可视化条件/阈值、中文展示、编辑、层级说明。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Alerts.vue')
s = io.open(P, encoding='utf-8').read()

# 1) 区块标题与术语说明
s = s.replace('<h4 style="margin:0">规则引擎</h4>',
              '<h4 style="margin:0">规则引擎（规则集 → 规则）</h4>', 1)
s = s.replace("""        <el-tag size="small" type="info">阈值告警由「已发布」的规则集产生</el-tag>""",
"""        <el-tag size="small" type="info">规则集 = 一组规则；规则 = 一条判定</el-tag>""", 1)
s = s.replace("""      <el-table :data="rulesets" v-loading="rsLoading" border size="small"
                highlight-current-row @current-change="onPickRuleset">""",
"""      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="层级关系：先建「规则集」（可理解为某一场景的规则包），再在其中加「规则」（单条阈值判定）；规则集发布后生效，旧版本自动停用。" />
      <el-table :data="rulesets" v-loading="rsLoading" border size="small"
                highlight-current-row :current-row-key="currentRuleset?.id"
                row-key="id" @current-change="onPickRuleset">""", 1)

# 2) 规则表：条件/阈值中文展示 + 编辑按钮
OLD_RULES_TABLE = """        <el-table :data="rules" border size="small">
          <el-table-column prop="ruleCode" label="规则编码" width="160" />
          <el-table-column prop="ruleName" label="名称" min-width="150" />
          <el-table-column prop="conditionExpr" label="条件" min-width="180"
                           show-overflow-tooltip />
          <el-table-column prop="thresholdJson" label="阈值" min-width="150"
                           show-overflow-tooltip />
          <el-table-column prop="severity" label="级别" width="100">
            <template #default="{ row }">{{ enumLabel('alertLevel', row.severity) }}</template>
          </el-table-column>"""
NEW_RULES_TABLE = """        <el-table :data="rules" border size="small">
          <el-table-column prop="ruleCode" label="规则编码" width="150" />
          <el-table-column prop="ruleName" label="名称" min-width="140" />
          <el-table-column label="条件" min-width="190" show-overflow-tooltip>
            <template #default="{ row }">{{ humanCondition(row.conditionExpr) }}</template>
          </el-table-column>
          <el-table-column label="阈值" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ humanThreshold(row.thresholdJson) }}</template>
          </el-table-column>
          <el-table-column prop="severity" label="级别" width="90">
            <template #default="{ row }">{{ enumLabel('alertLevel', row.severity) }}</template>
          </el-table-column>"""
if OLD_RULES_TABLE in s:
    s = s.replace(OLD_RULES_TABLE, NEW_RULES_TABLE, 1)

s = s.replace("""          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link :type="row.ruleStatus === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleRule(row)">
                {{ row.ruleStatus === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>""",
"""          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRule(row)">编辑</el-button>
              <el-button link :type="row.ruleStatus === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleRule(row)">
                {{ row.ruleStatus === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>""", 1)

# 3) 规则弹窗：改结构化输入
OLD_DIALOG_START = """    <!-- 新增规则 -->
    <el-dialog v-model="ruleVisible" title="新增规则" width="580px">
      <el-form :model="rf2" label-width="110px">
        <el-form-item label="规则编码" required>
          <el-input v-model="rf2.code" placeholder="如 OVERDUE_30" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="rf2.name" />
        </el-form-item>
        <el-form-item label="条件表达式">
          <el-input v-model="rf2.conditionExpr" placeholder="如 actual > threshold" />
        </el-form-item>
        <el-form-item label="阈值 JSON" required>
          <el-input v-model="rf2.thresholdJson" type="textarea" :rows="3"
                    placeholder='{"overdueDays":30}' />
        </el-form-item>
        <el-form-item label="严重级别">
          <el-select v-model="rf2.severity" style="width:100%">
            <el-option label="提示" value="INFO" />
            <el-option label="警告" value="WARNING" />
            <el-option label="严重" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="动作 JSON">
          <el-input v-model="rf2.actionsJson" type="textarea" :rows="2"
                    placeholder='{"notify":["org_manager"]}' />
        </el-form-item>
        <el-form-item label="优先级">
          <el-input-number v-model="rf2.priority" :min="1" style="width:100%" />
        </el-form-item>
      </el-form>"""
NEW_DIALOG_START = """    <!-- 新增/编辑规则 -->
    <el-dialog v-model="ruleVisible" :title="rf2.id ? '编辑规则' : '新增规则'" width="620px">
      <el-form :model="rf2" label-width="110px">
        <el-form-item label="规则编码" required>
          <el-input v-model="rf2.code" placeholder="如 OVERDUE_30" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="rf2.name" placeholder="如 逾期超 30 天告警" />
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
                title="只需选字段、运算符与阈值；条件表达式与阈值 JSON 会自动生成，无需手写。" />"""
if OLD_DIALOG_START in s:
    s = s.replace(OLD_DIALOG_START, NEW_DIALOG_START, 1)

# 4) 脚本：字段定义、生成、中文展示、编辑保存
OLD_SCRIPT_HEAD = """const rf2 = reactive({ code: '', name: '', conditionExpr: '', thresholdJson: '',
  severity: 'WARNING', actionsJson: '', priority: 10 })"""
NEW_SCRIPT_HEAD = """const RULE_FIELDS = [
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
  const m = String(expr).match(/^\\s*(\\w+)\\s*(>=|<=|>|<|=)\\s*([\\d.]+)\\s*$/)
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
}"""
if OLD_SCRIPT_HEAD in s:
    s = s.replace(OLD_SCRIPT_HEAD, NEW_SCRIPT_HEAD, 1)

# openRule 支持编辑
s = s.replace("""function openRule() {
  Object.assign(rf2, { code: '', name: '', conditionExpr: '', thresholdJson: '',
    severity: 'WARNING', actionsJson: '', priority: 10 })
  ruleVisible.value = true
}""",
"""function openRule(row) {
  if (row) {
    // 从已有条件反解字段/运算符/阈值，便于编辑
    const m = String(row.conditionExpr || '').match(/^\\s*(\\w+)\\s*(>=|<=|>|<|=)\\s*([\\d.]+)/)
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
}""", 1)

# doAddRule → 支持新增/编辑
OLD_SAVE = """async function doAddRule() {
  if (!rf2.code || !rf2.name || !rf2.thresholdJson) {
    ElMessage.warning('规则编码、名称、阈值 JSON 为必填'); return
  }
  try {
    JSON.parse(rf2.thresholdJson)
  } catch (e) {
    ElMessage.warning('阈值必须是合法 JSON，如 {"overdueDays":30}'); return
  }
  if (rf2.actionsJson) {
    try { JSON.parse(rf2.actionsJson) } catch (e) {
      ElMessage.warning('动作 JSON 格式不合法'); return
    }
  }
  saving.value = true
  try {
    await req.post(`/rules/rulesets/${currentRuleset.value.id}/rules`, { ...rf2 })
    ElMessage.success('规则已新增')
    ruleVisible.value = false
    viewRules(currentRuleset.value)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '新增失败')
  } finally { saving.value = false }
}"""
NEW_SAVE = """async function doAddRule() {
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
}"""
if OLD_SAVE in s:
    s = s.replace(OLD_SAVE, NEW_SAVE, 1)

# 默认选中第一个规则集
s = s.replace("""async function loadRulesets() {
  rsLoading.value = true
  try {
    rulesets.value = await req.get('/rules/rulesets', {
      params: { domain: rsDomain.value || undefined, status: rsStatus.value || undefined }
    }) || []
  } catch (e) {
    rulesets.value = []
  } finally { rsLoading.value = false }
}""",
"""async function loadRulesets() {
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
}""", 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Alerts.vue 规则引擎已可视化')
