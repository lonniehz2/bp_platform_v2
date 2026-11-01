<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('opsX.title') }}</h3>
      <el-tag size="small" type="info">{{ t('ops.extraTag') }}</el-tag>
      <div class="spacer" />
      <el-button @click="refresh">{{ t('opsX.refresh') }}</el-button>
    </div>

    <el-tabs v-model="tab">
      <!-- ================= 消息待办 ================= -->
      <el-tab-pane :label="t('opsX.msgTab')" name="msg">
        <div class="toolbar">
          <UserSelect v-model="msg.userId" width="210px" testid="userselect" />
          <el-input v-model="msgKeyword" :placeholder="t('opsX.keyword')" clearable style="width:210px"
                    data-testid="oe-msg-keyword" @keyup.enter="loadTodos" />
          <el-select v-model="msgStatus" :placeholder="t('opsX.status')" clearable style="width:120px">
            <el-option :label="t('opsX.pending')" value="PENDING" />
            <el-option :label="t('opsX.done')" value="DONE" />
          </el-select>
          <el-button type="primary" @click="loadTodos" data-testid="oe-msg-search">{{ t('opsX.search') }}</el-button>
          <el-button @click="resetMsgQuery" data-testid="oe-msg-reset">{{ t('opsX.reset') }}</el-button>
          <div class="spacer" />
          <el-button type="success" @click="openMsgSend()">{{ t('opsX.sendMsg') }}</el-button>
          <el-button @click="broadcast">{{ t('opsX.broadcast') }}</el-button>
          <el-button @click="retryFailed">{{ t('opsX.retryFailed') }}</el-button>
          <el-button @click="openTodoCreate()">{{ t('opsX.addTodo') }}</el-button>
        </div>
        <el-table :data="todos" border size="small" max-height="420">
          <el-table-column prop="title" :label="t('opsX.titleCol')" min-width="180" />
          <el-table-column prop="todoType" :label="t('opsX.type')" width="120" />
          <el-table-column :label="t('opsX.statusCol')" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.todoStatus === 'DONE' ? 'success'
                : (row.todoStatus === 'READ' ? 'info' : 'warning')">
                {{ enumLabel('todoStatus', row.todoStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('opsX.actions')" width="170">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('opsX.detail') }}</el-button>
              <el-button link type="primary" @click="markRead(row)">{{ t('opsX.markRead') }}</el-button>
              <el-button link type="success" @click="markDone(row)">{{ t('opsX.markDone') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 规则引擎 ================= -->
      <el-tab-pane :label="t('opsX.ruleTab')" name="rule">
        <div class="toolbar">
          <el-button type="success" @click="openRulesetCreate()">{{ t('opsX.addRuleset') }}</el-button>
          <el-button @click="openRuleCreate()">{{ t('opsX.addRule') }}</el-button>
          <el-button @click="loadRulesets">{{ t('opsX.refresh') }}</el-button>
        </div>
        <el-table :data="rulesets" border size="small" max-height="420">
          <el-table-column prop="code" :label="t('opsX.code')" width="150" />
          <el-table-column prop="name" :label="t('opsX.name')" min-width="160" />
          <el-table-column prop="domain" :label="t('opsX.domain')" width="120" />
          <el-table-column prop="rulesetStatus" :label="t('opsX.statusCol')" width="110">
            <template #default="{ row }">
              <el-tag size="small">{{ enumLabel('status', row.rulesetStatus) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('opsX.actions')" width="300" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="publishRuleset(row)">{{ t('opsX.publish') }}</el-button>
              <el-button link type="warning" @click="disableRuleset(row)">{{ t('opsX.disable') }}</el-button>
              <el-button link @click="openRuleFor(row)">{{ t('opsX.addRuleTo') }}</el-button>
              <el-button link type="success" @click="execRuleset(row)">{{ t('opsX.execTest') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 开放平台 ================= -->
      <el-tab-pane :label="t('opsX.openTab')" name="open">
        <div class="toolbar">
          <el-button @click="loadOpen">{{ t('opsX.refreshApps') }}</el-button>
          <el-button type="success" @click="openHookCreate()">{{ t('opsX.addWebhook') }}</el-button>
          <el-button @click="openHookList">{{ t('opsX.hookList') }}</el-button>
        </div>
        <el-table :data="apps" border size="small" max-height="420">
          <el-table-column prop="appName" :label="t('opsX.appName')" min-width="150" />
          <el-table-column prop="appCode" :label="t('opsX.appCode')" width="160" />
          <el-table-column :label="t('common.status')" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.appStatus === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('appStatus', row.appStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="toggleApp(row)">{{ t('opsX.toggle') }}</el-button>
              <el-button link type="warning" @click="resetSecret(row)">{{ t('opsX.resetSecret') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 权限管理 ================= -->
      <el-tab-pane :label="t('opsX.rbacTab')" name="rbac">
        <div class="toolbar">
          <el-button type="success" @click="openUserCreate()">{{ t('opsX.addUser') }}</el-button>
          <el-button @click="openRoleCreate()">{{ t('opsX.addRole') }}</el-button>
          <el-button @click="openPermCreate()">{{ t('opsX.addPerm') }}</el-button>
          <el-button @click="loadRbac">{{ t('opsX.refresh') }}</el-button>
        </div>
        <el-row :gutter="12">
          <el-col :span="8">
            <h4>用户</h4>
            <el-table :data="users" border size="small" max-height="360">
              <el-table-column prop="username" :label="t('opsX.username')" width="110" />
              <el-table-column prop="realName" :label="t('opsX.realName')" width="100" />
              <el-table-column label="操作" width="110">
                <template #default="{ row }">
                  <el-button link type="primary" @click="grantUserRoles(row)">{{ t('opsX.grantRoles') }}</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-col>
          <el-col :span="8">
            <h4>角色</h4>
            <el-table :data="roles" border size="small" max-height="360">
              <el-table-column prop="roleCode" :label="t('opsX.roleCode')" width="110" />
              <el-table-column prop="roleName" :label="t('opsX.roleName')" min-width="100" />
              <el-table-column label="操作" width="110">
                <template #default="{ row }">
                  <el-button link type="primary" @click="grantRolePerms(row)">{{ t('opsX.grantPerms') }}</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-col>
          <el-col :span="8">
            <h4>权限</h4>
            <el-table :data="perms" border size="small" max-height="360">
              <el-table-column prop="permCode" :label="t('opsX.permCode')" min-width="140" />
              <el-table-column prop="permName" :label="t('opsX.permName')" width="110" />
            </el-table>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ================= 通行授权 ================= -->
      <el-tab-pane :label="t('opsX.grantTab')" name="grant">
        <div class="toolbar">
          <el-button @click="loadGrants">{{ t('opsX.refresh') }}</el-button>
        </div>
        <el-table :data="grants" border size="small" max-height="440">
          <el-table-column prop="personId" :label="t('opsX.person')" width="180">
            <template #default="{ row }">{{ row.personName || row.personId }}</template>
          </el-table-column>
          <el-table-column :label="t('opsX.level')" width="110">
            <template #default="{ row }">{{ enumLabel('grantLevel', row.grantLevel) }}</template>
          </el-table-column>
          <el-table-column prop="validStart" :label="t('opsX.validStart')" width="160" />
          <el-table-column prop="validEnd" :label="t('opsX.validEnd')" width="160" />
          <el-table-column :label="t('common.status')" width="110">
            <template #default="{ row }">{{ enumLabel('grantStatus', row.grantStatus) }}</template>
          </el-table-column>
          <el-table-column :label="t('common.operation')" width="130">
            <template #default="{ row }">
              <el-button link type="danger" @click="revokeGrant(row)">{{ t('opsX.revoke') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 日房态 ================= -->
      <el-tab-pane :label="t('opsX.calendarTab')" name="calendar">
        <div class="toolbar">
          <HouseSelect v-model="cal.houseId" width="210px" testid="houseselect" />
          <el-date-picker v-model="cal.month" type="month" value-format="YYYY-MM"
                          :placeholder="t('opsX.month')" style="width:140px" />
          <el-button type="primary" @click="ensureCalendar">{{ t('opsX.genCalendar') }}</el-button>
          <div class="spacer" />
          <el-button @click="openCalPrice()">{{ t('misc.calendar.price') }}</el-button>
          <el-button @click="openCalStatus()">{{ t('misc5.detail') }}</el-button>
          <el-button @click="openCalBook()">{{ t('opsX.book') }}</el-button>
          <el-button @click="openCalRelease()">{{ t('opsX.release') }}</el-button>
        </div>
        <el-table :data="calendar" border size="small" max-height="420">
          <el-table-column prop="calendarDate" :label="t('opsX.date')" width="130" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">{{ enumLabel('dayStatus', row.dayStatus) }}</template>
          </el-table-column>
          <el-table-column prop="price" :label="t('opsX.price')" width="110" />
          <el-table-column prop="orderId" :label="t('opsX.order')" width="180" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 通用参数弹窗：按示例结构自动生成表单，不再让用户手写 JSON -->
    <el-dialog v-model="jsonVisible" :title="jsonTitle" width="700px">
      <el-alert type="info" :closable="false" show-icon :title="jsonHint" />
      <el-form :model="jsonForm" label-width="150px" style="margin-top:10px">
        <el-form-item v-for="(k, i) in jsonKeys" :key="k" :label="k">
          <el-input v-if="jsonKinds[k] === 'object'" v-model="jsonForm[k]" type="textarea"
                    :rows="3" style="font-family:monospace"
                    :data-testid="'f-' + k" />
          <el-switch v-else-if="jsonKinds[k] === 'boolean'" v-model="jsonForm[k]"
                     :data-testid="'f-' + k" />
          <el-input v-else-if="jsonKinds[k] === 'number'" v-model.number="jsonForm[k]"
                    type="number" :data-testid="'f-' + k" />
          <el-input v-else v-model="jsonForm[k]" :data-testid="'f-' + k" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="jsonVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="submitJson">{{ t('common.submit') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pickVisible" :title="pickTitle" width="480px">
      <el-input v-model="pickValue" placeholder="输入 ID，多个用英文逗号分隔" />
      <template #footer>
        <el-button @click="pickVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="submitPick">{{ t('common.submit') }}</el-button>
      </template>
    </el-dialog>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import { ref, reactive, onMounted, watch } from 'vue'
import DetailView from '@/components/DetailView.vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import HouseSelect from '@/components/HouseSelect.vue'
import UserSelect from '@/components/UserSelect.vue'
import { enumLabel } from '@/constants/enums'

/**
 * tab 与路由双向同步：每个 tab 都有独立 URL（/ops-extras/rule）
 * 好处：可直接分享/收藏某个 tab，刷新后停在原 tab，也便于后续拆分子菜单。
 */
const TABS = ['msg', 'rule', 'open', 'rbac', 'grant', 'calendar']
const route = useRoute()
const router = useRouter()
const tab = ref(TABS.includes(route.params.tab) ? route.params.tab : 'msg')
watch(() => route.params.tab, (v) => {
  const t = TABS.includes(v) ? v : 'msg'
  if (t !== tab.value) tab.value = t
})
watch(tab, (v) => {
  if (route.params.tab !== v) router.replace('/ops-extras/' + v)
})
const saving = ref(false)

// 消息
const todos = ref([])
const msg = reactive({ userId: 1 })

// 规则
const rulesets = ref([])
const currentRuleset = ref(null)

// 开放
const apps = ref([])

// RBAC
const users = ref([])
const roles = ref([])
const perms = ref([])

// 授权
const grants = ref([])

// 房态
const calendar = ref([])
const cal = reactive({ houseId: null, month: '' })

// 通用参数 / 选择弹窗
const jsonVisible = ref(false)
const jsonTitle = ref('')
const jsonHint = ref('')
/** 按示例结构自动生成表单：keys 决定字段，kinds 决定控件类型 */
const msgKeyword = ref('')
const msgStatus = ref('')
const jsonForm = reactive({})
const jsonKinds = reactive({})
const jsonKeys = ref([])
const jsonPath = ref('')
const pickVisible = ref(false)
const pickTitle = ref('')
const pickValue = ref('')
const pickPath = ref('')
const pickAfter = ref(null)


// ---------- 各模块「新增」入口（统一走 JSON 弹窗，字段取自后端 DTO） ----------
function openMsgSend() {
  openJson('发送消息', '按模板发送；接收人类型 PERSON/USER/ORG',
    '/messages/send',
    { templateCode: 'CONTRACT_EFFECTIVE', bizType: 'CONTRACT', bizId: 1,
      channel: 'INNER', receiverType: 'PERSON', receiverId: '1',
      title: '标题', content: '内容' })
}
function openTodoCreate() {
  openJson('新增待办', '给指定用户生成一条待办',
    '/messages/todos',
    { userId: 1, todoType: 'APPROVAL', title: '待办标题', content: '内容',
      bizType: 'APPLICATION', bizId: 1, dueTime: '2026-12-31 18:00:00' })
}
function openRulesetCreate() {
  openJson('新增规则集', '规则集是阈值规则的容器，发布后才参与评估',
    '/rules/rulesets',
    { code: 'RS_FIN_2', name: '欠费规则集', domain: 'FINANCE',
      scenario: 'ARREAR', securityType: 'PUBLIC', version: 'v1',
      description: '说明' })
}
function openRuleCreate() {
  if (!currentRuleset.value) {
    ElMessage.warning('请先在规则集行内点「加规则」')
    return
  }
  openJson('新增规则', '条件表达式 + 阈值 JSON',
    `/rules/rulesets/${currentRuleset.value.id}/rules`,
    { code: 'R_ARREAR_1', name: '欠费比例告警', conditionExpr: 'arrearRate > 15',
      thresholdJson: '{"threshold":15}', severity: 'WARNING',
      eventType: 'ARREAR_RATE' })
}
function openHookCreate() {
  openJson('新增 Webhook', '事件类型用英文逗号分隔',
    '/open/webhooks',
    { hookName: '测试回调', callbackUrl: 'https://example.com/cb',
      eventTypes: 'contract.effective', retryTimes: 3, hookStatus: 'ENABLED' })
}
function openUserCreate() {
  openJson('新增用户', '密码走 PBKDF2 加密存储',
    '/rbac/users',
    { username: 'newuser', password: 'Passw0rd!', realName: '新用户',
      orgId: 1, userType: 'STAFF' })
}
function openRoleCreate() {
  openJson('新增角色', 'dataScope：ALL / DEPT / SELF',
    '/rbac/roles',
    { roleCode: 'AUDITOR', roleName: '稽核员', dataScope: 'ALL' })
}
function openPermCreate() {
  openJson('新增权限', 'permType：API / MENU / BUTTON / DATA',
    '/rbac/permissions',
    { parentId: null, permCode: 'fin:audit:view', permName: '稽核查账',
      permType: 'API', routePath: '', sortNo: 99 })
}
function openCalPrice() {
  if (!cal.houseId) { ElMessage.warning('请先填房源ID'); return }
  openJson('修改日房价', '指定日期改价',
    `/house-calendar/${cal.houseId}/price`,
    { date: '2026-11-01', price: 220.00 })
}
function openCalStatus() {
  if (!cal.houseId) { ElMessage.warning('请先填房源ID'); return }
  openJson('修改日房态', 'dayStatus：AVAILABLE / BOOKED / OCCUPIED / CLOSED / MAINTENANCE',
    `/house-calendar/${cal.houseId}/status`,
    { start: '2026-11-01', end: '2026-11-01', dayStatus: 'MAINTENANCE',
      remark: '维修停用' })
}
function openCalBook() {
  openJson('预订房态', '短租预订占用某段日期',
    '/house-calendar/book',
    { houseId: 1, checkIn: '2026-11-01', checkOut: '2026-11-03',
      bookingId: 1, guestName: '客人' })
}
function openCalRelease() {
  openJson('释放房态', '取消预订/占用',
    '/house-calendar/release',
    { houseId: 1, checkIn: '2026-11-01', checkOut: '2026-11-03',
      bookingId: 1 })
}

function openJson(title, hint, path, sample) {
  jsonTitle.value = title
  jsonHint.value = hint
  jsonPath.value = path
  // 用示例结构生成表单：对象/数组当 JSON 文本编辑，其余按类型给控件
  jsonKeys.value = Object.keys(sample || {})
  for (const k of jsonKeys.value) {
    delete jsonForm[k]
    const v = sample[k]
    if (v !== null && typeof v === 'object') {
      jsonKinds[k] = 'object'
      jsonForm[k] = JSON.stringify(v)
    } else if (typeof v === 'boolean') {
      jsonKinds[k] = 'boolean'
      jsonForm[k] = v
    } else if (typeof v === 'number') {
      jsonKinds[k] = 'number'
      jsonForm[k] = v
    } else {
      jsonKinds[k] = 'string'
      jsonForm[k] = v === null || v === undefined ? '' : String(v)
    }
  }
  jsonVisible.value = true
}

async function submitJson() {
  const body = {}
  for (const k of jsonKeys.value) {
    if (jsonKinds[k] === 'object') {
      try {
        body[k] = JSON.parse(jsonForm[k] || 'null')
      } catch (e) {
        ElMessage.error('字段 ' + k + ' 的 JSON 格式错误'); return
      }
    } else {
      body[k] = jsonForm[k]
    }
  }
  saving.value = true
  try {
    await req.post(jsonPath.value, body)
    ElMessage.success('提交成功')
    jsonVisible.value = false
    refresh()
  } finally { saving.value = false }
}

function openPick(title, path, after) {
  pickTitle.value = title
  pickPath.value = path
  pickValue.value = ''
  pickAfter.value = after
  pickVisible.value = true
}

async function submitPick() {
  const ids = pickValue.value.split(',').map((x) => Number(x.trim()))
    .filter((x) => !Number.isNaN(x))
  if (!ids.length) { ElMessage.warning('请输入至少一个 ID'); return }
  saving.value = true
  try {
    await req.post(pickPath.value, { ids })
    ElMessage.success('已提交')
    pickVisible.value = false
    refresh()
  } finally { saving.value = false }
}

// ---------- 消息 ----------
async function loadTodos() {
  try {
    const d = await req.get('/messages/todos', {
      params: {
        pageNum: 1, pageSize: 50,
        userId: msg.userId || undefined,
        keyword: msgKeyword.value || undefined,
        status: msgStatus.value || undefined
      }
    })
    todos.value = d.rows || d || []
  } catch (e) { todos.value = [] }
}

/** 清空待办筛选 */
function resetMsgQuery() {
  msgKeyword.value = ''
  msgStatus.value = ''
  loadTodos()
}
function markRead(row) {
  return req.post(`/messages/todos/${row.id}/read`).then(() => {
    ElMessage.success('已读'); loadTodos()
  })
}
function markDone(row) {
  return req.post(`/messages/todos/${row.id}/done`).then(() => {
    ElMessage.success('已办结'); loadTodos()
  })
}
function broadcast() {
  openJson('批量广播', '按业务类型向相关人推送通知', '/messages/broadcast',
    { bizType: 'SYSTEM', title: '系统通知', content: '内容', bizId: 0 })
}
async function retryFailed() {
  const r = await req.post('/messages/retry-failed', null, { params: { limit: 20 } })
  ElMessage.success('重推完成：' + (r?.count ?? r ?? '已执行'))
}

// ---------- 规则 ----------
async function loadRulesets() {
  try {
    const d = await req.get('/rules/rulesets')
    rulesets.value = Array.isArray(d) ? d : (d.rows || [])
  } catch (e) { rulesets.value = [] }
}
function publishRuleset(row) {
  return req.post(`/rules/rulesets/${row.id}/publish`).then(() => {
    ElMessage.success('已发布'); loadRulesets()
  })
}
function disableRuleset(row) {
  return req.post(`/rules/rulesets/${row.id}/disable`).then(() => {
    ElMessage.success('已停用'); loadRulesets()
  })
}
function openRuleFor(row) {
  currentRuleset.value = row
  ruleVisible.value = true
}
function execRuleset(row) {
  openJson('执行规则集（测试）', '传入实际值立即评估，不落业务单据',
    `/rules/rulesets/${row.id}/execute`,
    { bizType: 'ARREAR', bizId: 1, actual: 15.5, count: 1, eventType: 'TEST' })
}

// ---------- 开放 ----------
async function loadOpen() {
  try {
    const d = await req.get('/open/apps')
    apps.value = Array.isArray(d) ? d : (d.rows || [])
  } catch (e) { apps.value = [] }
}
async function toggleApp(row) {
  const next = row.appStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  await req.post(`/open/apps/${row.id}/status`, { status: next })
  ElMessage.success('已' + (next === 'ENABLED' ? '启用' : '停用')); loadOpen()
}
async function resetSecret(row) {
  const { value } = await ElMessageBox.prompt('确认重置密钥？旧密钥立即失效',
    '重置密钥', { type: 'warning', inputValue: '确认' })
  if (value !== '确认') return
  const r = await req.post(`/open/apps/${row.id}/reset-secret`)
  ElMessageBox.alert('新密钥：' + (r?.appSecret || r), '请立即保存')
}
async function openHookList() {
  const d = await req.get('/open/webhooks')
  const list = Array.isArray(d) ? d : (d.rows || [])
  ElMessageBox.alert('Webhook 共 ' + list.length + ' 个\n'
    + list.map((x) => `${x.hookName} → ${x.callbackUrl} [${x.hookStatus}]`).join('\n')
    || '暂无', 'Webhook 列表')
}

// ---------- RBAC ----------
async function loadRbac() {
  try {
    const u = await req.get('/rbac/users', { params: { pageNum: 1, pageSize: 50 } })
    users.value = u.rows || u || []
  } catch (e) { users.value = [] }
  try {
    const r = await req.get('/rbac/roles')
    roles.value = Array.isArray(r) ? r : (r.rows || [])
  } catch (e) { roles.value = [] }
  try {
    const p = await req.get('/rbac/permissions')
    perms.value = Array.isArray(p) ? p : (p.rows || [])
  } catch (e) { perms.value = [] }
}
function grantUserRoles(row) {
  openPick(`给用户「${row.username}」授权角色`, `/rbac/users/${row.id}/roles`)
}
function grantRolePerms(row) {
  openPick(`给角色「${row.roleName}」授权权限`, `/rbac/roles/${row.id}/permissions`)
}

// ---------- 授权 ----------
async function loadGrants() {
  try {
    const d = await req.get('/grants', { params: { pageNum: 1, pageSize: 50 } })
    grants.value = d.rows || d || []
  } catch (e) { grants.value = [] }
}
async function revokeGrant(row) {
  const { value } = await ElMessageBox.prompt('撤销原因', '撤销通行授权',
    { type: 'warning' })
  await req.post(`/grants/${row.id}/revoke`, { reason: value })
  ElMessage.success('已撤销'); loadGrants()
}

// ---------- 房态 ----------
async function ensureCalendar() {
  if (!cal.houseId || !cal.month) { ElMessage.warning('请填房源ID与月份'); return }
  await req.post(`/house-calendar/${cal.houseId}/ensure`, null, {
    params: { month: cal.month }
  })
  ElMessage.success('已生成'); loadCalendar()
}
async function loadCalendar() {
  if (!cal.houseId) return
  try {
    const d = await req.get(`/house-calendar/${cal.houseId}`)
    calendar.value = Array.isArray(d) ? d : (d.rows || [])
  } catch (e) { calendar.value = [] }
}

function refresh() {
  if (tab.value === 'msg') loadTodos()
  else if (tab.value === 'rule') loadRulesets()
  else if (tab.value === 'open') loadOpen()
  else if (tab.value === 'rbac') loadRbac()
  else if (tab.value === 'grant') loadGrants()
  else loadCalendar()
}

onMounted(() => { loadTodos(); loadRulesets(); loadOpen(); loadRbac(); loadGrants() })
</script>
