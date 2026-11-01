<template>
  <div class="ops-page">
    <header class="ops-header">
      <div class="brand">
        <div class="logo"><span /></div>
        <div>
          <b>平台运营台</b>
          <span class="sub">Platform Operations Console</span>
        </div>
      </div>
      <div class="spacer" />
      <span class="who">{{ operatorName }}</span>
      <el-button text @click="pwdVisible = true">{{ t('platform.changePwd') }}</el-button>
      <el-button text @click="logout">{{ t('platform.logout') }}</el-button>
    </header>

    <main class="ops-main">
      <el-tabs v-model="tab">
        <el-tab-pane :label="t('platform.platformTab')" name="platforms">
          <div class="toolbar">
            <el-input v-model="query.keyword" :placeholder="t('platform.keyword')" clearable
                      style="width:200px" @keyup.enter="load" />
            <el-select v-model="query.status" :placeholder="t('platform.status')" clearable style="width:130px">
              <el-option :label="t('platform.enabled')" value="ENABLED" />
              <el-option :label="t('platform.disabled')" value="DISABLED" />
              <el-option :label="t('platform.archived')" value="ARCHIVED" />
            </el-select>
            <el-button type="primary" @click="load">{{ t('platform.search') }}</el-button>
            <el-button @click="resetQuery">{{ t('platform.reset') }}</el-button>
            <div class="spacer" />
            <el-button type="success" @click="openCreate">{{ t('platform.create') }}</el-button>
          </div>

          <el-table :data="rows" v-loading="loading" border size="small"
                    empty-text="暂无平台，点击右上角「新建平台」">
            <el-table-column prop="tenantCode" :label="t('platform.code')" width="130" />
            <el-table-column prop="tenantName" :label="t('platform.name')" min-width="180" show-overflow-tooltip />
            <el-table-column :label="t('platform.type')" width="100">
              <template #default="{ row }">{{ typeText(row.tenantType) }}</template>
            </el-table-column>
            <el-table-column prop="regionCode" :label="t('platform.region')" width="100" />
            <el-table-column :label="t('platform.status')" width="100">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'ENABLED' ? 'success'
                  : (row.status === 'ARCHIVED' ? 'info' : 'warning')">
                  {{ statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="adminCount" :label="t('platform.admin')" width="80" align="right" />
            <el-table-column prop="createTime" :label="t('platform.created')" width="160" />
            <el-table-column :label="t('platform.actions')" width="230" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDetail(row)">{{ t('platform.detail') }}</el-button>
                <el-button v-if="row.status === 'ENABLED'" link type="warning"
                           @click="setStatus(row, 'disable')">停用</el-button>
                <el-button v-if="row.status === 'DISABLED'" link type="success"
                           @click="setStatus(row, 'enable')">启用</el-button>
                <el-button v-if="row.status === 'DISABLED'" link type="danger"
                           @click="archive(row)">归档</el-button>
                <el-button v-if="row.status === 'ARCHIVED'" link type="success"
                           @click="restore(row)">恢复</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane :label="t('platform.auditTab')" name="audits">
          <div class="toolbar">
            <el-button @click="loadAudits">{{ t('platform.refresh') }}</el-button>
          </div>
          <el-table :data="audits" border size="small" empty-text="暂无审计记录">
            <el-table-column prop="createTime" :label="t('platform.time')" width="170" />
            <el-table-column prop="operatorName" :label="t('platform.operator')" width="120" />
            <el-table-column prop="platformCode" :label="t('platform.platform')" width="120" />
            <el-table-column prop="action" :label="t('platform.action')" width="170" />
            <el-table-column prop="detail" :label="t('platform.detailCol')" min-width="220" show-overflow-tooltip />
            <el-table-column prop="ip" label="IP" width="130" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </main>

    <!-- 新建平台 -->
    <el-dialog v-model="createVisible" :title="t('platform.createTitle')" width="560px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item :label="t('platform.name')" required>
          <el-input v-model="createForm.tenantName" maxlength="100" :placeholder="t('platform.name')" />
        </el-form-item>
        <el-form-item :label="t('platform.regionCode')" required>
          <el-input v-model="createForm.regionCode" maxlength="6"
                    :placeholder="t('platform.regionHint')" />
        </el-form-item>
        <el-form-item :label="t('platform.platformType')">
          <el-select v-model="createForm.tenantType" style="width:100%">
            <el-option :label="t('platform.gov')" value="GOV" />
            <el-option :label="t('platform.org')" value="ORG" />
            <el-option :label="t('platform.enterprise')" value="ENTERPRISE" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('platform.contact')">
          <el-input v-model="createForm.contactName" />
        </el-form-item>
        <el-form-item :label="t('platform.phone')">
          <el-input v-model="createForm.contactPhone" />
        </el-form-item>
        <el-divider content-position="left">平台管理员</el-divider>
        <el-form-item :label="t('platform.adminUsername')" required>
          <el-input v-model="createForm.adminUsername" :placeholder="t('platform.adminUsernameHint')" />
        </el-form-item>
        <el-form-item :label="t('platform.adminName')">
          <el-input v-model="createForm.adminRealName" />
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon
                  title="平台编码将按「行政区划 + 3 位序列」自动生成；初始密码仅在创建成功后显示一次。" />
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('platform.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="createPlatform">{{ t('platform.createBtn') }}</el-button>
      </template>
    </el-dialog>

    <!-- 创建结果 / 初始密码 -->
    <el-dialog v-model="resultVisible" :title="t('platform.passwordTitle')" width="460px">
      <el-alert type="warning" :closable="false" show-icon
                title="请立即复制并通过安全渠道交给对应人员；关闭后无法再次查看。" />
      <el-descriptions :column="1" border size="small" style="margin-top:12px">
        <el-descriptions-item :label="t('platform.code')">{{ result.code || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('platform.name')">{{ result.name || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('platform.adminAccount')">{{ result.username }}</el-descriptions-item>
        <el-descriptions-item :label="t('platform.initialPwd')">
          <b style="letter-spacing:1px">{{ result.password }}</b>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="copyPwd">{{ t('platform.copyPwd') }}</el-button>
        <el-button type="primary" @click="resultVisible = false">{{ t('platform.saved') }}</el-button>
      </template>
    </el-dialog>

    <!-- 平台详情 -->
    <el-drawer v-model="detailVisible" :title="t('platform.detailTitle')" size="720px">
      <div v-if="current">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="平台编码">{{ current.tenantCode }}</el-descriptions-item>
          <el-descriptions-item label="平台名称">{{ current.tenantName }}</el-descriptions-item>
          <el-descriptions-item :label="t('platform.type')">{{ typeText(current.tenantType) }}</el-descriptions-item>
          <el-descriptions-item :label="t('platform.region')">{{ current.regionCode }}</el-descriptions-item>
          <el-descriptions-item :label="t('platform.status')">{{ statusText(current.status) }}</el-descriptions-item>
          <el-descriptions-item :label="t('platform.created')">{{ current.createTime }}</el-descriptions-item>
          <el-descriptions-item :label="t('platform.contact')">{{ current.contactName || '—' }}</el-descriptions-item>
          <el-descriptions-item :label="t('platform.phone')">{{ current.contactPhone || '—' }}</el-descriptions-item>
        </el-descriptions>

        <div class="toolbar" style="margin-top:16px">
          <b>平台管理员</b>
          <div class="spacer" />
          <el-button type="primary" plain size="small" @click="openAddAdmin">{{ t('platform.addAdmin') }}</el-button>
        </div>
        <el-table :data="admins" border size="small" empty-text="暂无管理员">
          <el-table-column prop="username" :label="t('platform.username')" width="130" />
          <el-table-column prop="realName" :label="t('platform.realName')" width="110" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">{{ row.status === 'ENABLED' ? '启用' : '停用' }}</template>
          </el-table-column>
          <el-table-column :label="t('platform.pendingPwd')" width="80">
            <template #default="{ row }">{{ row.mustChangePassword ? '是' : '否' }}</template>
          </el-table-column>
          <el-table-column prop="lastLoginTime" :label="t('platform.lastLogin')" width="160" />
          <el-table-column :label="t('platform.actions')" width="240" fixed="right">
            <template #default="{ row }">
              <el-button link type="warning" @click="resetPwd(row)">{{ t('platform.resetPwd') }}</el-button>
              <el-button v-if="row.status === 'ENABLED'" link type="danger"
                         @click="setAdmin(row, 'disable')">停用</el-button>
              <el-button v-else link type="success"
                         @click="setAdmin(row, 'enable')">启用</el-button>
              <el-button v-if="row.lockedUntil" link @click="unlock(row)">{{ t('platform.unlock') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <!-- 新增管理员 -->
    <el-dialog v-model="addAdminVisible" :title="t('platform.addAdminTitle')" width="460px">
      <el-form :model="adminForm" label-width="90px">
        <el-form-item :label="t('platform.username')" required><el-input v-model="adminForm.username" /></el-form-item>
        <el-form-item :label="t('platform.realName')"><el-input v-model="adminForm.realName" /></el-form-item>
        <el-form-item :label="t('platform.phone')"><el-input v-model="adminForm.phone" /></el-form-item>
        <el-form-item :label="t('platform.email')"><el-input v-model="adminForm.email" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addAdminVisible = false">{{ t('platform.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="addAdmin">{{ t('platform.createBtn') }}</el-button>
      </template>
    </el-dialog>

    <!-- 修改密码 -->
    <el-dialog v-model="pwdVisible" :title="t('platform.changePwdTitle')" width="440px"
               :close-on-click-modal="false">
      <el-form :model="pwdForm" label-width="90px">
        <el-form-item :label="t('platform.oldPwd')"><el-input v-model="pwdForm.oldPassword" type="password" show-password /></el-form-item>
        <el-form-item :label="t('platform.newPwd')"><el-input v-model="pwdForm.newPassword" type="password" show-password /></el-form-item>
        <el-form-item :label="t('platform.confirmPwd')"><el-input v-model="pwdForm.confirm" type="password" show-password /></el-form-item>
      </el-form>
      <el-alert v-if="forcePwd" type="warning" :closable="false" show-icon
                title="首次登录必须修改密码后才能继续操作。" />
      <template #footer>
        <el-button v-if="!forcePwd" @click="pwdVisible = false">{{ t('platform.cancel') }}</el-button>
        <el-button type="primary" @click="changePwd">{{ t('platform.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  operatorApi, getOperatorToken, getOperatorName, setOperatorToken, setOperatorName
} from '@/api/operator'

const { t } = useI18n()
const router = useRouter()
const operatorName = ref(getOperatorName() || '运营管理员')
const tab = ref('platforms')
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const audits = ref([])
const query = reactive({ keyword: '', status: '' })

const createVisible = ref(false)
const resultVisible = ref(false)
const detailVisible = ref(false)
const addAdminVisible = ref(false)
const pwdVisible = ref(false)
const forcePwd = ref(sessionStorage.getItem('bp.operator.mustChange') === '1')
const current = ref(null)
const admins = ref([])

const createForm = reactive({
  tenantName: '', regionCode: '', tenantType: 'GOV', contactName: '', contactPhone: '',
  adminUsername: 'admin', adminRealName: ''
})
const result = reactive({ code: '', name: '', username: '', password: '' })
const adminForm = reactive({ username: '', realName: '', phone: '', email: '' })
const pwdForm = reactive({ oldPassword: '', newPassword: '', confirm: '' })

function typeText(t) {
  return { GOV: '政府', ORG: '运营机构', ENTERPRISE: '企业' }[t] || t || '—'
}
function statusText(s) {
  return { ENABLED: '启用', DISABLED: '停用', ARCHIVED: '已归档' }[s] || s
}

async function load() {
  loading.value = true
  try {
    rows.value = await operatorApi.platforms({
      keyword: query.keyword || undefined, status: query.status || undefined
    })
  } finally { loading.value = false }
}

function resetQuery() {
  query.keyword = ''
  query.status = ''
  load()
}

function openCreate() {
  Object.assign(createForm, {
    tenantName: '', regionCode: '', tenantType: 'GOV', contactName: '', contactPhone: '',
    adminUsername: 'admin', adminRealName: ''
  })
  createVisible.value = true
}

async function createPlatform() {
  if (!createForm.tenantName || !createForm.regionCode || !createForm.adminUsername) {
    ElMessage.warning('请填写平台名称、行政区划和管理员账号')
    return
  }
  saving.value = true
  try {
    const d = await operatorApi.createPlatform({ ...createForm })
    Object.assign(result, {
      code: d.platform.tenantCode, name: d.platform.tenantName,
      username: d.adminUsername, password: d.initialPassword
    })
    createVisible.value = false
    resultVisible.value = true
    load()
  } finally { saving.value = false }
}

function copyPwd() {
  navigator.clipboard?.writeText(result.password)
  ElMessage.success('密码已复制')
}

async function setStatus(row, mode) {
  const label = mode === 'enable' ? '启用' : '停用'
  await ElMessageBox.confirm(`确认${label}平台「${row.tenantName}」？`, `${label}平台`,
    { type: 'warning' })
  await operatorApi[mode](row.id)
  ElMessage.success(`已${label}`)
  load()
}

async function archive(row) {
  const { value } = await ElMessageBox.prompt(
    `归档后该平台不可登录，且不物理删除。请输入平台编码「${row.tenantCode}」确认：`,
    '归档平台', { type: 'warning', inputValidator: (v) => v === row.tenantCode || '编码不一致' })
  if (value !== row.tenantCode) return
  await operatorApi.archive(row.id)
  ElMessage.success('已归档')
  load()
}

async function restore(row) {
  await ElMessageBox.confirm('恢复后平台为「停用」状态，需再手动启用。确认恢复？', '恢复平台')
  await operatorApi.restore(row.id)
  ElMessage.success('已恢复')
  load()
}

async function openDetail(row) {
  current.value = await operatorApi.platform(row.id)
  admins.value = await operatorApi.admins(row.id)
  detailVisible.value = true
}

function openAddAdmin() {
  Object.assign(adminForm, { username: '', realName: '', phone: '', email: '' })
  addAdminVisible.value = true
}

async function addAdmin() {
  if (!adminForm.username) { ElMessage.warning('请输入账号'); return }
  saving.value = true
  try {
    const d = await operatorApi.createAdmin(current.value.id, { ...adminForm })
    addAdminVisible.value = false
    Object.assign(result, { code: current.value.tenantCode, name: current.value.tenantName,
      username: d.username, password: d.initialPassword })
    resultVisible.value = true
    admins.value = await operatorApi.admins(current.value.id)
  } finally { saving.value = false }
}

async function resetPwd(row) {
  await ElMessageBox.confirm(`重置「${row.username}」密码？`, '重置密码', { type: 'warning' })
  const d = await operatorApi.resetPwd(current.value.id, row.userId)
  Object.assign(result, { code: current.value.tenantCode, name: current.value.tenantName,
    username: d.username, password: d.initialPassword })
  resultVisible.value = true
  admins.value = await operatorApi.admins(current.value.id)
}

async function setAdmin(row, mode) {
  await operatorApi[mode === 'enable' ? 'enableAdmin' : 'disableAdmin'](current.value.id, row.userId)
  ElMessage.success(mode === 'enable' ? '已启用' : '已停用')
  admins.value = await operatorApi.admins(current.value.id)
}

async function unlock(row) {
  await operatorApi.unlockAdmin(current.value.id, row.userId)
  ElMessage.success('已解锁')
  admins.value = await operatorApi.admins(current.value.id)
}

async function loadAudits() {
  const d = await operatorApi.audits({ pageNum: 1, pageSize: 100 })
  audits.value = d.rows || []
}

async function changePwd() {
  if (!pwdForm.oldPassword || !pwdForm.newPassword) {
    ElMessage.warning('请填写原密码与新密码')
    return
  }
  if (pwdForm.newPassword !== pwdForm.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  await operatorApi.changePassword({
    oldPassword: pwdForm.oldPassword, newPassword: pwdForm.newPassword
  })
  ElMessage.success('密码已修改')
  sessionStorage.removeItem('bp.operator.mustChange')
  forcePwd.value = false
  pwdVisible.value = false
}

async function logout() {
  try { await operatorApi.logout() } catch (e) { /* ignore */ }
  setOperatorToken('')
  setOperatorName('')
  sessionStorage.removeItem('bp.operator.mustChange')
  router.replace('/platform-admin/login')
}

onMounted(async () => {
  document.documentElement.classList.add('dark')
  if (!getOperatorToken()) {
    router.replace('/platform-admin/login')
    return
  }
  await load()
  if (forcePwd.value) pwdVisible.value = true
})

onUnmounted(() => {
  document.documentElement.classList.remove('dark')
})
</script>

<style scoped>
.ops-page { min-height: 100vh; background: #0f141a; color: #e6f1ff; }
.ops-header {
  height: 56px; display: flex; align-items: center; gap: 12px;
  padding: 0 20px; background: #151b23; border-bottom: 1px solid #242d38;
}
.brand { display: flex; gap: 12px; align-items: center; }
.logo {
  width: 34px; height: 34px; border-radius: 10px;
  background: linear-gradient(145deg, #2b7bff, #12c2a0);
  display: flex; align-items: center; justify-content: center;
}
.logo span { width: 14px; height: 14px; border-radius: 4px; background: #eaf6ff; }
.brand b { font-size: 15px; }
.sub { display: block; font-size: 10px; color: #6f8fb3; letter-spacing: 1px; }
.spacer { flex: 1; }
.who { font-size: 12px; color: #9db8d6; margin-right: 8px; }
.ops-main { padding: 18px 20px; }
.ops-main :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: #1b232d;
  --el-table-header-text-color: #cfe3ff;
  --el-table-text-color: #dbe9f7;
  --el-table-border-color: #242d38;
  --el-table-row-hover-bg-color: #1e2833;
}
.ops-main :deep(.el-table th.el-table__cell) { background: #1b232d !important; }
.toolbar { display: flex; gap: 8px; align-items: center; margin-bottom: 12px; }
:deep(.el-tabs__item) { color: #9db8d6; }
:deep(.el-tabs__item.is-active) { color: #59d9ff; }
</style>
