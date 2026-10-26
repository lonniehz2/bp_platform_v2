# -*- coding: utf-8 -*-
"""P2-3 告警处理页：增加「规则引擎」区块（规则集 + 规则 + 发布/启停）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# 枚举：subsidyMode 补全（原只有 FIXED/RATIO）
P = os.path.join(ROOT, 'frontend', 'src', 'constants', 'enums.js')
e = io.open(P, encoding='utf-8').read()
if "BY_AREA: '按面积'" not in e:
    e = e.replace("  subsidyMode: { FIXED: '定额', RATIO: '按比例' },",
                  """  subsidyMode: {
    FIXED: '定额', BY_AREA: '按面积', BY_PERSON: '按人', RATIO: '按租金比例'
  },
  rulesetStatus: { DRAFT: '草稿', PUBLISHED: '已发布', DISABLED: '已停用' },
  ruleStatus: { ENABLED: '启用', DISABLED: '停用' },""", 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(e)
    print('enums 已补 subsidyMode / rulesetStatus / ruleStatus')

# ---------------- Alerts.vue ----------------
P2 = os.path.join(ROOT, 'frontend', 'src', 'views', 'Alerts.vue')
s = io.open(P2, encoding='utf-8').read()

TPL = """
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
"""

if '规则引擎' not in s:
    s = s.replace("""    <el-drawer v-model="drawerVisible\"""", TPL + """    <el-drawer v-model="drawerVisible\"""", 1)

SCRIPT = """
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
"""

if 'loadRulesets' not in s:
    s = s.replace('</script>', SCRIPT + '</script>', 1)

io.open(P2, 'w', encoding='utf-8', newline='').write(s)
print('Alerts.vue 已加规则引擎区块')
