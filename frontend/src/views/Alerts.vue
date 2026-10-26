<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">告警处理</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="关键字" clearable style="width:160px"
                @keyup.enter="reload" />
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button @click="loadStats">告警统计</el-button>
      <el-button type="success" @click="createVisible = true">新建告警</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon :title="'阈值告警由规则引擎产生；可转工单、升级或忽略'"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="alertType" label="告警类型" width="150">
        <template #default="{ row }">{{ row.alertTypeLabel || enumLabel('alertType', row.alertType) }}</template>
      </el-table-column>
      <el-table-column prop="alertLevel" label="级别" width="100">
        <template #default="{ row }">{{ row.alertLevelLabel || enumLabel('alertLevel', row.alertLevel) }}</template>
      </el-table-column>
      <el-table-column prop="alertStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.alertStatusLabel || enumLabel('alertStatus', row.alertStatus) }}</template>
      </el-table-column>
      <el-table-column prop="alertContent" label="内容" width="200" />
      <el-table-column label="操作" width="424" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/handle', '处理')">处理</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/resolve', '解决')">解决</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/ignore', '忽略')">忽略</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/escalate', '升级')">升级</el-button>
          <el-button link type="warning" @click="actAction(row, '/api/v1/alerts/{id}/to-workorder', '转工单')">转工单</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <!-- ==================== 规则引擎 ==================== -->
    <div class="page-card">
      <div class="toolbar">
        <h4 style="margin:0">规则引擎</h4>
        <el-tag size="small" type="info">阈值告警由「已发布」的规则集产生</el-tag>
        <div class="spacer" />
        <el-select v-model="rsDomain" placeholder="域" clearable style="width:130px"
                   @change="loadRulesets">
          <el-option label="告警" value="ALERT" />
          <el-option label="计费" value="BILLING" />
          <el-option label="信用" value="CREDIT" />
        </el-select>
        <el-select v-model="rsStatus" placeholder="状态" clearable style="width:120px"
                   @change="loadRulesets">
          <el-option label="草稿" value="DRAFT" />
          <el-option label="已发布" value="PUBLISHED" />
          <el-option label="已停用" value="DISABLED" />
        </el-select>
        <el-button @click="loadRulesets">刷新</el-button>
        <el-button type="success" @click="openRuleset">新建规则集</el-button>
      </div>

      <el-table :data="rulesets" v-loading="rsLoading" border size="small"
                highlight-current-row @current-change="onPickRuleset">
        <el-table-column prop="rulesetCode" label="规则集编码" width="170" />
        <el-table-column prop="rulesetName" label="名称" min-width="160" />
        <el-table-column prop="domain" label="域" width="100" />
        <el-table-column prop="scenario" label="场景" width="130" />
        <el-table-column prop="rulesetVersion" label="版本" width="80" />
        <el-table-column prop="rulesetStatus" label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.rulesetStatus === 'PUBLISHED' ? 'success'
              : (row.rulesetStatus === 'DISABLED' ? 'info' : 'warning')">
              {{ enumLabel('rulesetStatus', row.rulesetStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewRules(row)">查看规则</el-button>
            <el-button link type="success" :disabled="row.rulesetStatus === 'PUBLISHED'"
                       @click="publishRuleset(row)">发布</el-button>
            <el-button link type="warning" :disabled="row.rulesetStatus === 'DISABLED'"
                       @click="disableRuleset(row)">停用</el-button>
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
                     @click="openRule">新增规则</el-button>
        </div>
        <el-table :data="rules" border size="small">
          <el-table-column prop="ruleCode" label="规则编码" width="160" />
          <el-table-column prop="ruleName" label="名称" min-width="150" />
          <el-table-column prop="conditionExpr" label="条件" min-width="180"
                           show-overflow-tooltip />
          <el-table-column prop="thresholdJson" label="阈值" min-width="150"
                           show-overflow-tooltip />
          <el-table-column prop="severity" label="级别" width="100">
            <template #default="{ row }">{{ enumLabel('alertLevel', row.severity) }}</template>
          </el-table-column>
          <el-table-column prop="priority" label="优先级" width="90" />
          <el-table-column prop="ruleStatus" label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.ruleStatus === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('ruleStatus', row.ruleStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link :type="row.ruleStatus === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleRule(row)">
                {{ row.ruleStatus === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="!rules.length" class="muted" style="margin-top:8px">该规则集暂无规则</div>
      </div>
    </div>

    <!-- 新建规则集 -->
    <el-dialog v-model="rulesetVisible" title="新建规则集" width="560px">
      <el-form :model="rs" label-width="110px">
        <el-form-item label="编码" required>
          <el-input v-model="rs.code" placeholder="如 ALERT_OVERDUE" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="rs.name" />
        </el-form-item>
        <el-form-item label="域" required>
          <el-select v-model="rs.domain" style="width:100%">
            <el-option label="告警" value="ALERT" />
            <el-option label="计费" value="BILLING" />
            <el-option label="信用" value="CREDIT" />
          </el-select>
        </el-form-item>
        <el-form-item label="场景">
          <el-input v-model="rs.scenario" placeholder="如 OVERDUE_BILL" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="rs.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="同编码再次创建会自动递增版本；新版本为草稿，发布后旧版本自动停用" />
      <template #footer>
        <el-button @click="rulesetVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateRuleset">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增规则 -->
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
      </el-form>
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
            <el-input v-model="form.orgId" /></el-form-item></el-col>
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
            <el-input v-model="form.houseId" /></el-form-item></el-col>
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
/** 通用详情弹窗（复用 DetailView，字段与中文名来自后端字段字典） */
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
                 { handleUserId: 1, action: label, result: value })
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
const rf2 = reactive({ code: '', name: '', conditionExpr: '', thresholdJson: '',
  severity: 'WARNING', actionsJson: '', priority: 10 })

async function loadRulesets() {
  rsLoading.value = true
  try {
    rulesets.value = await req.get('/rules/rulesets', {
      params: { domain: rsDomain.value || undefined, status: rsStatus.value || undefined }
    }) || []
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

function openRule() {
  Object.assign(rf2, { code: '', name: '', conditionExpr: '', thresholdJson: '',
    severity: 'WARNING', actionsJson: '', priority: 10 })
  ruleVisible.value = true
}

async function doAddRule() {
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
