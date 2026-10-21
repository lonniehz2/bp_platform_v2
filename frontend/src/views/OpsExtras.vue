<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">扩展操作台</h3>
      <el-tag size="small" type="info">消息 · 规则 · 开放 · 权限 · 授权 · 房态</el-tag>
      <div class="spacer" />
      <el-button @click="refresh">刷新</el-button>
    </div>

    <el-tabs v-model="tab">
      <!-- ================= 消息待办 ================= -->
      <el-tab-pane label="消息待办" name="msg">
        <div class="toolbar">
          <el-input v-model="msg.userId" placeholder="用户ID" style="width:150px" />
          <el-button @click="loadTodos">查询待办</el-button>
          <div class="spacer" />
          <el-button type="success" @click="openMsgSend()">发送消息</el-button>
          <el-button @click="broadcast">批量广播</el-button>
          <el-button @click="retryFailed">重推失败</el-button>
          <el-button @click="openTodoCreate()">新增待办</el-button>
        </div>
        <el-table :data="todos" border size="small" max-height="420">
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="todoType" label="类型" width="120" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.todoStatus === 'DONE' ? 'success'
                : (row.todoStatus === 'READ' ? 'info' : 'warning')">
                {{ enumLabel('todoStatus', row.todoStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="170">
            <template #default="{ row }">
              <el-button link type="primary" @click="markRead(row)">标记已读</el-button>
              <el-button link type="success" @click="markDone(row)">办结</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 规则引擎 ================= -->
      <el-tab-pane label="告警规则" name="rule">
        <div class="toolbar">
          <el-button type="success" @click="openRulesetCreate()">新增规则集</el-button>
          <el-button @click="openRuleCreate()">新增规则</el-button>
          <el-button @click="loadRulesets">刷新</el-button>
        </div>
        <el-table :data="rulesets" border size="small" max-height="420">
          <el-table-column prop="code" label="编码" width="150" />
          <el-table-column prop="name" label="名称" min-width="160" />
          <el-table-column prop="domain" label="领域" width="120" />
          <el-table-column prop="rulesetStatus" label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small">{{ enumLabel('status', row.rulesetStatus) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="publishRuleset(row)">发布</el-button>
              <el-button link type="warning" @click="disableRuleset(row)">停用</el-button>
              <el-button link @click="openRuleFor(row)">加规则</el-button>
              <el-button link type="success" @click="execRuleset(row)">执行测试</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 开放平台 ================= -->
      <el-tab-pane label="开放平台" name="open">
        <div class="toolbar">
          <el-button @click="loadOpen">刷新应用</el-button>
          <el-button type="success" @click="openHookCreate()">新增 Webhook</el-button>
          <el-button @click="openHookList">Webhook 列表</el-button>
        </div>
        <el-table :data="apps" border size="small" max-height="420">
          <el-table-column prop="appName" label="应用名称" min-width="150" />
          <el-table-column prop="appCode" label="应用编码" width="160" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="row.appStatus === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('appStatus', row.appStatus) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="toggleApp(row)">启停</el-button>
              <el-button link type="warning" @click="resetSecret(row)">重置密钥</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 权限管理 ================= -->
      <el-tab-pane label="权限管理" name="rbac">
        <div class="toolbar">
          <el-button type="success" @click="openUserCreate()">新增用户</el-button>
          <el-button @click="openRoleCreate()">新增角色</el-button>
          <el-button @click="openPermCreate()">新增权限</el-button>
          <el-button @click="loadRbac">刷新</el-button>
        </div>
        <el-row :gutter="12">
          <el-col :span="8">
            <h4>用户</h4>
            <el-table :data="users" border size="small" max-height="360">
              <el-table-column prop="username" label="账号" width="110" />
              <el-table-column prop="realName" label="姓名" width="100" />
              <el-table-column label="操作" width="110">
                <template #default="{ row }">
                  <el-button link type="primary" @click="grantUserRoles(row)">授权角色</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-col>
          <el-col :span="8">
            <h4>角色</h4>
            <el-table :data="roles" border size="small" max-height="360">
              <el-table-column prop="roleCode" label="编码" width="110" />
              <el-table-column prop="roleName" label="名称" min-width="100" />
              <el-table-column label="操作" width="110">
                <template #default="{ row }">
                  <el-button link type="primary" @click="grantRolePerms(row)">授权权限</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-col>
          <el-col :span="8">
            <h4>权限</h4>
            <el-table :data="perms" border size="small" max-height="360">
              <el-table-column prop="permCode" label="权限码" min-width="140" />
              <el-table-column prop="permName" label="名称" width="110" />
            </el-table>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- ================= 通行授权 ================= -->
      <el-tab-pane label="授权撤销" name="grant">
        <div class="toolbar">
          <el-button @click="loadGrants">刷新</el-button>
        </div>
        <el-table :data="grants" border size="small" max-height="440">
          <el-table-column prop="personId" label="人员" width="180">
            <template #default="{ row }">{{ row.personName || row.personId }}</template>
          </el-table-column>
          <el-table-column label="层级" width="110">
            <template #default="{ row }">{{ enumLabel('grantLevel', row.grantLevel) }}</template>
          </el-table-column>
          <el-table-column prop="validStart" label="生效" width="160" />
          <el-table-column prop="validEnd" label="失效" width="160" />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">{{ enumLabel('grantStatus', row.grantStatus) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="130">
            <template #default="{ row }">
              <el-button link type="danger" @click="revokeGrant(row)">撤销</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 日房态 ================= -->
      <el-tab-pane label="日房态" name="calendar">
        <div class="toolbar">
          <el-input v-model="cal.houseId" placeholder="房源ID" style="width:180px" />
          <el-date-picker v-model="cal.month" type="month" value-format="YYYY-MM"
                          placeholder="月份" style="width:140px" />
          <el-button type="primary" @click="ensureCalendar">生成当月房态</el-button>
          <div class="spacer" />
          <el-button @click="openCalPrice()">改价</el-button>
          <el-button @click="openCalStatus()">改状态</el-button>
          <el-button @click="openCalBook()">预订</el-button>
          <el-button @click="openCalRelease()">释放</el-button>
        </div>
        <el-table :data="calendar" border size="small" max-height="420">
          <el-table-column prop="calendarDate" label="日期" width="130" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">{{ enumLabel('dayStatus', row.dayStatus) }}</template>
          </el-table-column>
          <el-table-column prop="price" label="价格" width="110" />
          <el-table-column prop="orderId" label="订单" width="180" />
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
        <el-button @click="jsonVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitJson">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pickVisible" :title="pickTitle" width="480px">
      <el-input v-model="pickValue" placeholder="输入 ID，多个用英文逗号分隔" />
      <template #footer>
        <el-button @click="pickVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitPick">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
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
      params: { pageNum: 1, pageSize: 50, userId: msg.userId || undefined }
    })
    todos.value = d.rows || d || []
  } catch (e) { todos.value = [] }
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
