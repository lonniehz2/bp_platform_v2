<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('rbac.title') }}</h3>
      <el-tag size="small" type="info">{{ t('rbacX.flow') }}</el-tag>
      <div class="spacer" />
      <el-button type="primary" @click="load">{{ t('rbac.refresh') }}</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon
              :title="t('rbacX.adminTip')"
              style="margin-bottom:12px" />

    <el-tabs v-model="tab">
      <!-- ================= 用户 ================= -->
      <el-tab-pane :label="t('rbac.userTab')" name="user">
        <div class="toolbar">
          <el-button type="success" @click="userVisible = true">{{ t('rbac.newUser') }}</el-button>
          <el-input v-model="ukeyword" :placeholder="t('rbac.keyword')" clearable style="width:180px"
                    data-testid="rbac-user-keyword" @keyup.enter="load" />
          <el-button type="primary" @click="load">{{ t('rbac.search') }}</el-button>
          <el-button @click="resetUserQuery" data-testid="rbac-user-reset">{{ t('rbac.reset') }}</el-button>
          <span class="muted">{{ t('rbacX.count', { n: users.length }) }}</span>
        </div>
        <el-table :data="users" v-loading="loading" border size="small" max-height="460">
          <el-table-column prop="username" :label="t('rbac.username')" width="140" />
          <el-table-column prop="realName" :label="t('rbac.realName')" width="120" />
          <el-table-column :label="t('rbac.roles')" min-width="180">
            <template #default="{ row }">
              <span v-if="row.roleNames">{{ row.roleNames }}</span>
              <span v-else class="muted">{{ t('rbacX.unassigned') }}</span>
            
</template>
          </el-table-column>
          <el-table-column prop="orgId" :label="t('rbac.org')" width="180">
            <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>


          </el-table-column>
          <el-table-column :label="t('rbac.type')" width="110">
            <template #default="{ row }">{{ enumLabel('userType', row.userType) }}</template>
          </el-table-column>
          <el-table-column :label="t('rbac.status')" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('status', row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('rbac.admin')" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.isAdmin == 1" size="small" type="danger">{{ t('rbacX.yes') }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('rbac.actions')" width="300" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openUserDetail(row)">{{ t('rbac.detail') }}</el-button>
              <el-button link type="primary" @click="openUserEdit(row)">{{ t('rbac.edit') }}</el-button>
              <el-button link type="primary" @click="openGrantRoles(row)">{{ t('rbac.grantRoles') }}</el-button>
              <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleUserStatus(row)">
                {{ row.status === 'ENABLED' ? t('rbacX.disable') : t('rbacX.enable') }}
              </el-button>
              <el-button link type="danger" @click="removeUser(row)">{{ t('rbac.delete') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 角色 ================= -->
      <el-tab-pane :label="t('rbac.roleTab')" name="role">
        <div class="toolbar">
          <el-button type="success" @click="roleVisible = true">{{ t('rbac.newRole') }}</el-button>
          <el-input v-model="rkeyword" :placeholder="t('rbac.roleKeyword')" clearable style="width:180px"
                    data-testid="rbac-role-keyword" @keyup.enter="load" />
          <el-button type="primary" @click="load">{{ t('rbacX.search') }}</el-button>
          <el-button @click="resetRoleQuery" data-testid="rbac-role-reset">{{ t('rbac.reset') }}</el-button>
          <span class="muted">{{ t('rbacX.count', { n: roles.length }) }}</span>
        </div>
        <el-table :data="roles" v-loading="loading" border size="small" max-height="460">
          <el-table-column prop="roleCode" :label="t('rbac.roleCode')" width="170" />
          <el-table-column prop="roleName" :label="t('rbac.roleName')" min-width="160" />
          <el-table-column :label="t('rbac.dataScope')" width="130">
            <template #default="{ row }">{{ enumLabel('dataScope', row.dataScope) }}</template>
          </el-table-column>
          <el-table-column :label="t('rbac.status')" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('status', row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('rbac.actions')" width="250" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRoleConfig(row)" data-testid="role-config">{{ t('rbac.configure') }}</el-button>
              <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleRoleStatus(row)">
                {{ row.status === 'ENABLED' ? t('common.disable') : t('common.enable') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 权限 ================= -->
      <el-tab-pane :label="t('rbac.permTab')" name="perm">
        <div class="toolbar">
          <el-button type="success" @click="permVisible = true">{{ t('rbac.newPerm') }}</el-button>
          <el-input v-model="pkeyword" :placeholder="t('rbac.permKeyword')" clearable style="width:180px"
                    data-testid="rbac-perm-keyword" @keyup.enter="load" />
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="resetPermQuery" data-testid="rbac-perm-reset">{{ t('rbac.reset') }}</el-button>
          <span class="muted">{{ t('rbacX.permCount', { n: perms.length }) }}</span>
        </div>
        <el-table :data="perms" v-loading="loading" border size="small" max-height="460">
          <el-table-column prop="permCode" :label="t('rbac.permCode')" width="240" />
          <el-table-column prop="permName" :label="t('rbac.permName')" min-width="150" />
          <el-table-column :label="t('rbacX.type')" width="110">
            <template #default="{ row }">{{ enumLabel('permType', row.permType) }}</template>
          </el-table-column>
          <el-table-column prop="routePath" :label="t('rbac.route')" width="170" />
          <el-table-column :label="t('rbac.status')" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('status', row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('rbacX.actions')" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                         @click="togglePermStatus(row)">
                {{ row.status === 'ENABLED' ? t('common.disable') : t('common.enable') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增用户 -->
    <el-dialog v-model="userVisible" :title="t('rbac.createUserTitle')" width="560px">
      <el-form :model="uf" label-width="110px">
        <el-form-item :label="t('rbac.account')" required>
          <el-input v-model="uf.username" :placeholder="t('rbac.accountHint')" /></el-form-item>
        <el-form-item :label="t('rbac.password')" required>
          <el-input v-model="uf.password" type="password" show-password
                    :placeholder="t('rbac.passwordHint')" /></el-form-item>
        <el-form-item :label="t('rbac.realName')" required>
          <el-input v-model="uf.realName" /></el-form-item>
        <el-form-item :label="t('rbac.org')" required>
          <el-select v-model="uf.orgId" filterable clearable style="width:100%"
                     :placeholder="t('rbac.org')" data-testid="user-org">
            <el-option v-for="o in orgOptions" :key="o.id"
                       :label="o.orgName" :value="String(o.id)" />
          </el-select></el-form-item>
        <el-form-item :label="t('rbac.roles')" required>
          <el-select v-model="uf.roleIds" multiple filterable style="width:100%"
                     :placeholder="t('rbacX.roleHint')"
                     data-testid="user-roles">
            <el-option v-for="r in roles" :key="r.id"
                       :label="`${r.roleName}（${r.roleCode}）`" :value="String(r.id)" />
          </el-select></el-form-item>
        <el-form-item :label="t('rbac.bindPerson')">
          <PersonPicker v-model="uf.personId" />
          <div class="muted" style="font-size:12px;line-height:1.5">
            {{ t('rbacX.roleScopeTip') }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userVisible = false">{{ t('rbac.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateUser">{{ t('rbac.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 新增角色 -->
    <el-dialog v-model="roleVisible" :title="t('rbac.roleCreateTitle')" width="500px">
      <el-form :model="rf" label-width="110px">
        <el-form-item :label="t('rbac.roleCode')" required>
          <el-input v-model="rf.roleCode" :placeholder="t('rbac.roleCodeHint')" />
        </el-form-item>
        <el-form-item :label="t('rbac.roleName')" required>
          <el-input v-model="rf.roleName" /></el-form-item>
        <el-form-item :label="t('rbac.dataScope')">
          <el-select v-model="rf.dataScope" style="width:100%">
            <el-option :label="t('rbac.scopeAllData')" value="ALL" />
            <el-option :label="t('rbac.scopeDept')" value="DEPT" />
            <el-option :label="t('rbac.scopeSelf')" value="SELF" />
          </el-select></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleVisible = false">{{ t('rbac.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateRole">{{ t('rbac.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 新增权限 -->
    <el-dialog v-model="permVisible" :title="t('rbac.permCreateTitle')" width="560px">
      <el-form :model="pf" label-width="110px">
        <el-form-item :label="t('rbac.permCode')" required>
          <el-input v-model="pf.permCode" :placeholder="t('rbacX.permCodeHint')" /></el-form-item>
        <el-form-item :label="t('rbac.permName')" required>
          <el-input v-model="pf.permName" /></el-form-item>
        <el-form-item :label="t('rbac.permType')">
          <el-select v-model="pf.permType" style="width:100%">
            <el-option :label="t('rbac.api')" value="API" />
            <el-option :label="t('rbac.menu')" value="MENU" />
            <el-option :label="t('rbac.button')" value="BUTTON" />
            <el-option :label="t('rbac.data')" value="DATA" />
          </el-select></el-form-item>
        <el-form-item :label="t('rbac.routePath')">
          <el-input v-model="pf.routePath" placeholder="/xxx" /></el-form-item>
        <el-form-item :label="t('rbacX.sort')">
          <el-input-number v-model="pf.sortNo" :min="1" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permVisible = false">{{ t('rbac.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreatePerm">{{ t('rbac.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 角色配置：基本信息 + 数据范围 + 权限，一页完成 -->
    <el-dialog v-model="roleCfgVisible" :title="t('rbacX.configTitle', { name: roleCfg.roleName || '' })" width="760px">
      <el-form :model="roleCfg" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item :label="t('rbac.roleCode')">
            <el-input :model-value="roleCfg.roleCode" disabled /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('rbac.roleName')">
            <el-input v-model="roleCfg.roleName" data-testid="role-cfg-name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('rbacX.dataScope')">
            <el-select v-model="roleCfg.dataScope" style="width:100%" data-testid="role-cfg-scope">
              <el-option :label="t('rbac.scopeAllData')" value="ALL" />
              <el-option :label="t('rbac.scopeOrg')" value="ORG" />
              <el-option :label="t('rbac.scopeOrgSub')" value="ORG_SUB" />
              <el-option :label="t('rbac.scopeSelf')" value="SELF" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item :label="t('rbacX.status')">
            <el-select v-model="roleCfg.status" style="width:100%">
              <el-option :label="t('rbac.enable')" value="ENABLED" />
              <el-option :label="t('rbac.disable')" value="DISABLED" />
            </el-select></el-form-item></el-col>
        </el-row>
      </el-form>

      <div class="toolbar" style="margin:4px 0 8px">
        <b>{{ t('rbacX.permConfig') }}</b>
        <span class="muted">{{ t('rbacX.selected', { n: checkedPerms.length, total: perms.length }) }}</span>
        <div class="spacer" />
        <el-button size="small" @click="checkAllPerms">{{ t('rbac.selectAll') }}</el-button>
        <el-button size="small" @click="checkedPerms = []">{{ t('rbac.clear') }}</el-button>
      </div>

      <el-tabs v-model="permTab" style="margin-top:4px">
        <el-tab-pane :label="t('rbac.pagePerm')" name="page">
          <div class="muted" style="margin-bottom:6px">
            {{ t('rbacX.menuHint') }}
          </div>
          <el-scrollbar max-height="330px">
            <div v-for="mg in pageMenuGroups" :key="mg.group" class="perm-group">
              <div class="perm-group-head">
                <el-checkbox
                  :model-value="mg.items.every((p) => checkedPerms.includes(String(p.id)))"
                  :indeterminate="!mg.items.every((p) => checkedPerms.includes(String(p.id)))
                    && mg.items.some((p) => checkedPerms.includes(String(p.id)))"
                  @change="(v) => toggleGroup(mg, v)">
                  {{ mg.group }}（{{ mg.items.length }}）
                </el-checkbox>
              </div>
              <div class="perm-actions">
                <el-checkbox
                  v-for="p in mg.items" :key="p.id"
                  :model-value="checkedPerms.includes(String(p.id))"
                  :label="p.permName"
                  :title="p.routePath || p.permCode"
                  @change="(v) => togglePerm(p, v)" />
              </div>
            </div>
          </el-scrollbar>
        </el-tab-pane>
        <el-tab-pane :label="t('rbac.funcPerm')" name="func">
          <div class="muted" style="margin-bottom:6px">
            {{ t('rbacX.actionHint') }}
          </div>
          <el-scrollbar max-height="330px">
        <div v-for="g in permGroups" :key="g.key" class="perm-group">
          <div class="perm-group-head">
            <el-checkbox
              :model-value="g.items.every((p) => checkedPerms.includes(String(p.id)))"
              :indeterminate="!g.items.every((p) => checkedPerms.includes(String(p.id)))
                && g.items.some((p) => checkedPerms.includes(String(p.id)))"
              @change="(v) => toggleGroup(g, v)">
              {{ g.label }}（{{ g.items.length }}）
            </el-checkbox>
          </div>
          <div class="perm-group-body">
            <div v-for="res in g.resources" :key="res.key" class="perm-res">
              <div class="perm-res-head">
                <el-checkbox
                  :model-value="res.items.every((p) => checkedPerms.includes(String(p.id)))"
                  :indeterminate="!res.items.every((p) => checkedPerms.includes(String(p.id)))
                    && res.items.some((p) => checkedPerms.includes(String(p.id)))"
                  @change="(v) => toggleGroup(res, v)">
                  {{ res.label }}
                </el-checkbox>
              </div>
              <div class="perm-actions">
                <el-checkbox
                  v-for="p in res.items" :key="p.id"
                  :model-value="checkedPerms.includes(String(p.id))"
                  :label="p.actionLabel || permLabel(p)"
                  :title="p.permCode"
                  @change="(v) => togglePerm(p, v)" />
              </div>
            </div>
          </div>
        </div>
          </el-scrollbar>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="roleCfgVisible = false">{{ t('rbac.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="saveRoleConfig">{{ t('rbac.save') }}</el-button>
      </template>
    </el-dialog>

    <!-- 授权关系 -->
    <el-dialog v-model="grantVisible" :title="grantTitle" width="480px">
      <el-alert type="info" :closable="false" show-icon
                :title="grantHint" />
      <el-select v-model="grantIds" multiple filterable style="width:100%;margin-top:12px"
                 :placeholder="grantPlaceholder">
        <el-option v-for="o in grantOptions" :key="o.value" :label="o.label"
                   :value="o.value" />
      </el-select>
      <template #footer>
        <el-button @click="grantVisible = false">{{ t('rbac.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doGrant">{{ t('rbac.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
    <el-dialog v-model="userDetailVisible" :title="t('rbac.userDetailTitle')" width="560px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item :label="t('rbac.account')">{{ userDetail.username }}</el-descriptions-item>
        <el-descriptions-item :label="t('rbac.realName')">{{ userDetail.realName || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('rbac.phone')">{{ userDetail.phone || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('rbac.email')">{{ userDetail.email || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('rbacX.status')">{{ enumLabel('status', userDetail.status) }}</el-descriptions-item>
        <el-descriptions-item :label="t('rbacX.type')">{{ enumLabel('userType', userDetail.userType) }}</el-descriptions-item>
        <el-descriptions-item :label="t('rbac.lastLogin')">{{ userDetail.lastLoginTime || '—' }}</el-descriptions-item>
        <el-descriptions-item :label="t('rbac.loginCount')">{{ userDetail.loginCount || 0 }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="userEditVisible" :title="t('rbacX.editUser')" width="520px">
      <el-form :model="userForm" label-width="90px">
        <el-form-item :label="t('rbacX.name')"><el-input v-model="userForm.realName" /></el-form-item>
        <el-form-item :label="t('rbacX.phone')"><el-input v-model="userForm.phone" /></el-form-item>
        <el-form-item :label="t('rbacX.email')"><el-input v-model="userForm.email" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userEditVisible = false">{{ t('rbacX.cancel') }}</el-button>
        <el-button type="primary" @click="saveUser">{{ t('rbacX.save') }}</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'
import PersonPicker from '@/components/PersonPicker.vue'

const { t } = useI18n()
const TABS = ['user', 'role', 'perm']
const route = useRoute()
const router = useRouter()
const tab = ref(TABS.includes(route.params.tab) ? route.params.tab : 'user')
watch(() => route.params.tab, (v) => {
  const t = TABS.includes(v) ? v : 'user'
  if (t !== tab.value) tab.value = t
})
watch(tab, (v) => {
  if (route.params.tab !== v) router.replace('/rbac/' + v)
})
const loading = ref(false)
const saving = ref(false)
const users = ref([])
/** 用户列表关键字筛选（后端 /rbac/users 支持 keyword） */
const ukeyword = ref('')
const rkeyword = ref('')
const pkeyword = ref('')
function resetRoleQuery() { rkeyword.value = ''; load() }
function resetPermQuery() { pkeyword.value = ''; load() }
function resetUserQuery() {
  ukeyword.value = ''
  load()
}
const roles = ref([])
const perms = ref([])

const userVisible = ref(false)
const roleVisible = ref(false)
const permVisible = ref(false)
const grantVisible = ref(false)

const uf = reactive({ username: '', password: '', realName: '', orgId: '', roleIds: [], personId: '' })
const rf = reactive({ roleCode: '', roleName: '', dataScope: 'ALL' })
const pf = reactive({ permCode: '', permName: '', permType: 'API',
  routePath: '', sortNo: 99 })

const grantTitle = ref('')
const grantHint = ref('')
const grantPlaceholder = ref('')
const grantIds = ref([])
const grantOptions = ref([])
const grantTarget = ref(null)
const grantKind = ref('')

async function load() {
  loading.value = true
  try {
    const u = await req.get('/rbac/users', {
      params: { keyword: ukeyword.value || undefined }
    })
    users.value = u.rows || u || []
  } catch (e) { users.value = [] }
  try {
    const r = await req.get('/rbac/roles', { params: { keyword: rkeyword.value || undefined } })
    roles.value = Array.isArray(r) ? r : (r.rows || [])
  } catch (e) { roles.value = [] }
  try {
    const p = await req.get('/rbac/permissions', { params: { keyword: pkeyword.value || undefined } })
    perms.value = Array.isArray(p) ? p : (p.rows || [])
  } catch (e) { perms.value = [] }
  loading.value = false
}

async function doCreateUser() {
  if (!uf.username || !uf.password || !uf.realName || !uf.orgId) {
    ElMessage.warning(t('rbacX.requiredUser')); return
  }
  if (!(uf.roleIds && uf.roleIds.length)) {
    ElMessage.warning(t('rbacX.requiredRole')); return
  }
  saving.value = true
  try {
    await req.post('/rbac/users', { ...uf, roleIds: uf.roleIds || [] })
    ElMessage.success(t('rbacX.createdUser'))
    userVisible.value = false; load()
  } finally { saving.value = false }
}

async function doCreateRole() {
  if (!rf.roleCode || !rf.roleName) {
    ElMessage.warning(t('rbacX.requiredRole2')); return
  }
  saving.value = true
  try {
    await req.post('/rbac/roles', { ...rf })
    ElMessage.success(t('rbacX.createdRole'))
    roleVisible.value = false; load()
  } finally { saving.value = false }
}

async function doCreatePerm() {
  if (!pf.permCode || !pf.permName) {
    ElMessage.warning(t('rbacX.requiredPerm')); return
  }
  saving.value = true
  try {
    await req.post('/rbac/permissions', { ...pf })
    ElMessage.success(t('rbacX.createdPerm'))
    permVisible.value = false; load()
  } finally { saving.value = false }
}

/** 给用户授权角色 */
async function openGrantRoles(row) {
  grantKind.value = 'user'
  grantTarget.value = row
  grantTitle.value = `给「${row.realName || row.username}」授权角色`
  grantHint.value = t('rbacX.grantHint')
  grantPlaceholder.value = t('rbacX.grantPlaceholder')
  grantOptions.value = roles.value.map((r) => ({
    value: String(r.id), label: `${r.roleName}（${r.roleCode}）`
  }))
  // 预填该用户已有角色，便于增减
  grantIds.value = []
  try {
    const cur = await req.get(`/rbac/users/${row.id}/roles`)
    const list = Array.isArray(cur) ? cur : (cur?.rows || [])
    grantIds.value = list.map((x) => String(x.id || x.roleId)).filter(Boolean)
  } catch (e) { /* 无权限或未配置时留空 */ }
  grantVisible.value = true
}

/** 给角色授权权限 */

/** 角色配置：基本信息 + 数据范围 + 权限 一页完成 */
const MODULE_LABEL = {
  iam: '用户与权限', person: '人员与档案', biz: '业务办理', fin: '财务',
  asset: '资产房源', ops: '运维工单', msg: '消息待办', sys: '系统配置',
  rpt: '报表统计', open: '开放平台', gov: '监管报送', alloc: '配租轮候',
  'access-records': '通行记录', auth: '认证会话', credit: '信用惩戒',
  credits: '信用惩戒', dev: '设备管理', files: '文件管理', grant: '通行授权',
  'grant-audit-logs': '授权审计', keyring: '钥匙管理', messages: '消息',
  orgs: '组织机构', platform: '平台管理', rbac: '用户与权限', rule: '计费规则',
  rules: '计费规则', 'short-rent-orders': '短租订单', test: '联调测试'
}

/** 权限动作字典（按钮/接口级） */
const PERM_ACTION_LABEL = {
  list: '查看', query: '查询', detail: '详情', create: '新增', update: '修改',
  delete: '删除', assign: '授权', audit: '审核', approve: '审批', export: '导出',
  publish: '发布', disable: '停用', enable: '启用', manage: '管理', revoke: '撤销',
  print: '打印', view: '查看', edit: '编辑', handle: '处理', submit: '提交',
  cancel: '作废', sign: '签约', grant: '授权', scan: '扫描', recalc: '重算',
  freeze: '冻结', unfreeze: '解冻', run: '执行', sync: '同步', send: '发送',
  broadcast: '广播', batch: '批量', reset: '重置', unlock: '解锁', confirm: '确认',
  reject: '驳回', allocate: '核销', waive: '减免', verify: '核验', execute: '执行',
  complete: '完成', import: '导入', download: '下载', upload: '上传'
}

/** 页面权限显示名：优先路由标题 */
function routeTitle(p) {
  const path = String(p.routePath || '')
  if (path) {
    const r = router.getRoutes().find((x) => x.path === path)
    if (r && r.meta && r.meta.title) return r.meta.title
  }
  return String(p.permName || '').replace(/^页面-/, '')
}

/** 功能权限显示名：模块 · 动作 */
function permLabel(p) {
  const parts = String(p.permCode || '').split(':')
  const mod = MODULE_LABEL[parts[0]]
  const act = PERM_ACTION_LABEL[parts[2]]
  if (mod && act) return mod + ' · ' + act
  if (act) return act
  return String(p.permName || p.permCode || '').replace(/^[a-z0-9-]+-/, '')
}


/** 用户详情 / 编辑 / 启停 / 删除 */
const userDetailVisible = ref(false)
const userDetail = ref({})
const userEditVisible = ref(false)
const userForm = reactive({ id: null, realName: '', phone: '', email: '', orgId: null })

function openUserDetail(row) {
  userDetail.value = row
  userDetailVisible.value = true
}

function openUserEdit(row) {
  Object.assign(userForm, {
    id: row.id, realName: row.realName, phone: row.phone,
    email: row.email, orgId: row.orgId
  })
  userEditVisible.value = true
}

async function saveUser() {
  try {
    await req.put(`/rbac/users/${userForm.id}`, { ...userForm })
    ElMessage.success('已保存')
    userEditVisible.value = false
    loadUsers()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  }
}

async function toggleUserStatus(row) {
  const next = row.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.post(`/rbac/users/${row.id}/status`, { status: next })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    loadUsers()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

async function removeUser(row) {
  try {
    await ElMessageBox.confirm(`确认删除用户「${row.username}」？`, '提示', { type: 'warning' })
    await req.delete(`/rbac/users/${row.id}`)
    ElMessage.success('已删除')
    loadUsers()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.message || '删除失败')
  }
}

/** 组织下拉选项（新增用户时必填，决定数据归属） */
const orgOptions = ref([])
async function loadOrgOptions() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = d.rows || d || []
  } catch (e) { orgOptions.value = [] }
}

const roleCfgVisible = ref(false)
const permTab = ref('page')
const roleCfg = reactive({ id: '', roleCode: '', roleName: '', dataScope: 'ALL', status: 'ENABLED' })
const checkedPerms = ref([])

/** 权限按模块分组（permCode 形如 biz:contract:create） */
/** 页面级权限（page:xxx:view）——对应菜单可见性 */
const pagePerms = computed(() =>
  perms.value.filter((p) => String(p.permCode || '').startsWith('page:'))
    .sort((a, b) => String(a.permName).localeCompare(String(b.permName), 'zh')))

/** 页面权限按左侧菜单分组呈现（分组顺序与侧边栏一致） */
const pageMenuGroups = computed(() => {
  const order = ['运营总览', '保障对象', '资格准入', '合同管理', '账务收费',
    '授权与交房', '服务与监督', '资产台账', '系统与集成', '其他']
  const map = new Map()
  for (const p of pagePerms.value) {
    const g = menuGroupOf(p.routePath)
    if (!map.has(g)) map.set(g, [])
    map.get(g).push(p)
  }
  return order.filter((g) => map.has(g)).map((g) => ({ group: g, key: g, items: map.get(g) }))
})

/** 路由 → 菜单分组（与 useMenu 的 CLASSIC_GROUP 对齐） */
function menuGroupOf(path) {
  const p = String(path || '')
  const G = {
    '/dashboard': '运营总览', '/reports': '运营总览', '/todos': '运营总览',
    '/persons': '保障对象', '/annual-reviews': '保障对象',
    '/applications': '资格准入', '/waitlist': '资格准入',
    '/allocations': '资格准入', '/publicities': '资格准入',
    '/contracts': '合同管理', '/contract-changes': '合同管理',
    '/exchanges': '合同管理', '/terminations': '合同管理',
    '/fee-items': '账务收费', '/bills': '账务收费', '/deposits': '账务收费',
    '/arrears': '账务收费', '/subsidies': '账务收费', '/cashflow': '账务收费',
    '/devices': '授权与交房', '/access': '授权与交房',
    '/keyring': '授权与交房', '/grants': '授权与交房',
    '/workorders': '服务与监督', '/complaints': '服务与监督',
    '/appeals': '服务与监督', '/visits': '服务与监督',
    '/credits': '服务与监督', '/alerts': '服务与监督', '/messages': '服务与监督',
    '/houses': '资产台账', '/spaces': '资产台账',
    '/house-calendar': '资产台账', '/short-rent': '资产台账',
    '/orgs': '系统与集成', '/rbac': '系统与集成', '/sys': '系统与集成',
    '/ops-center': '系统与集成', '/ops-extras': '系统与集成',
    '/open': '系统与集成', '/gov': '系统与集成'
  }
  return G[p] || '其他'
}

/** 功能权限（按钮/接口级），按模块→资源→操作分组 */
const permGroups = computed(() => {
  const map = new Map()
  for (const p of perms.value) {
    if (String(p.permCode || '').startsWith('page:')) continue
    const key = String(p.permCode || '').split(':')[0] || 'other'
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(p)
  }
  const RES_LABEL = {
    user: '用户', role: '角色', perm: '权限', contract: '合同', person: '人员',
    house: '房源', bill: '账单', feeItem: '计费项', deposit: '押金', arrear: '催缴',
    report: '报表', screen: '大屏', audit: '审计', dict: '字典', config: '参数',
    app: '应用', log: '日志', keyring: '钥匙', grant: '授权', visit: '走访',
    complaint: '投诉', appeal: '申诉', credit: '信用', alert: '告警', workorder: '工单',
    adapter: '适配器', test: '测试', manage: '管理', space: '空间', device: '设备',
    access: '通行', payment: '收款', refund: '退款', subsidy: '补贴', dunning: '催缴',
    reconcile: '对账', cashflow: '资金流水', exchange: '换房', termination: '退租',
    allocation: '配租', application: '申请', review: '年审', publicity: '公示',
    open: '开放平台', webhook: 'Webhook', screen2: '大屏',
  rules: '规则', credits: '信用', 'access-records': '通行记录',
  idle: '空置分析', trace: '轨迹', 'untrusted-ratio': '异常比例',
  verify: '核验', waitlist: '轮候', publicity: '公示', cohabitant: '同住人',
  annualReview: '年审', inspectionPlan: '巡检计划', todo: '待办',
  visits: '走访', dunning: '催缴', allotment: '配租', queue: '队列',
  metrics: '指标', sys: '系统', config: '参数', audit: '审计',
  command: '指令', report: '报表', billing: '计费', reconcile: '对账',
  cashflow: '资金流水', grants: '授权', keyring: '钥匙', alerts: '告警',
  complaints: '投诉', appeals: '申诉', visitsPlan: '走访计划',
  staff: '员工', tenant: '承租人', platform: '平台', role: '角色', perm: '权限'
  }
  const ACTION_LABEL = {
    list: '查看', query: '查询', detail: '详情', create: '新增', update: '修改',
    delete: '删除', assign: '授权', audit: '审核', approve: '审批', export: '导出',
    publish: '发布', disable: '停用', manage: '管理', revoke: '撤销', print: '打印',
    view: '查看', edit: '编辑', handle: '处理', submit: '提交', cancel: '作废',
    sign: '签约', grant: '授权', scan: '扫描', recalc: '重算', freeze: '冻结',
    unfreeze: '解冻', run: '执行', sync: '同步', send: '发送', broadcast: '广播'
  }
  return Array.from(map.entries())
    .map(([key, items]) => {
      // 模块内再按资源分组：permCode 形如 iam:user:list
      const byRes = new Map()
      for (const p of items) {
        const parts = String(p.permCode || '').split(':')
        const res = parts[1] || 'other'
        if (!byRes.has(res)) byRes.set(res, [])
        byRes.get(res).push({ ...p, actionLabel: PERM_ACTION_LABEL[parts[2]] || ACTION_LABEL[parts[2]] || parts[2] || '' })
      }
      const resources = Array.from(byRes.entries())
        .map(([rk, list]) => ({ key: rk,
  label: RES_LABEL[rk] || (/[\u4e00-\u9fa5]/.test(rk) ? rk : '其他'),
  items: list }))
        .sort((a, b) => a.key.localeCompare(b.key))
      return { key, label: MODULE_LABEL[key] || key, items, resources }
    })
    .sort((a, b) => a.key.localeCompare(b.key))
})

function togglePerm(p, on) {
  const id = String(p.id)
  if (on) {
    if (!checkedPerms.value.includes(id)) checkedPerms.value = [...checkedPerms.value, id]
  } else {
    checkedPerms.value = checkedPerms.value.filter((x) => x !== id)
  }
}

function toggleGroup(g, on) {
  const ids = g.items.map((p) => String(p.id))
  if (on) {
    checkedPerms.value = Array.from(new Set([...checkedPerms.value, ...ids]))
  } else {
    checkedPerms.value = checkedPerms.value.filter((x) => !ids.includes(x))
  }
}

function checkAllPerms() {
  checkedPerms.value = perms.value.map((p) => String(p.id))
}

/** 角色启用 / 停用 */
async function toggleRoleStatus(row) {
  const next = row.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.put(`/rbac/roles/${row.id}`, {
      roleName: row.roleName, dataScope: row.dataScope, status: next
    })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}


/** 权限码启用 / 停用 */
async function togglePermStatus(row) {
  const next = row.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.post(`/rbac/permissions/${row.id}/status`, { status: next })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

async function openRoleConfig(row) {
  roleCfg.id = row.id
  roleCfg.roleCode = row.roleCode
  roleCfg.roleName = row.roleName
  roleCfg.dataScope = row.dataScope || 'ALL'
  roleCfg.status = row.status || 'ENABLED'
  checkedPerms.value = []
  roleCfgVisible.value = true
  // 回显该角色已有权限
  try {
    const d = await req.get(`/rbac/roles/${row.id}/permissions`)
    const list = Array.isArray(d) ? d : (d?.rows || [])
    checkedPerms.value = list.map((x) => String(x.id || x))
  } catch (e) { /* 无回显接口时留空，由用户重选 */ }
}

async function saveRoleConfig() {
  if (!roleCfg.roleName) { ElMessage.warning('请填写角色名称'); return }
  saving.value = true
  try {
    await req.put(`/rbac/roles/${roleCfg.id}`, {
      roleName: roleCfg.roleName, dataScope: roleCfg.dataScope, status: roleCfg.status
    })
    await req.post(`/rbac/roles/${roleCfg.id}/permissions`, { ids: checkedPerms.value })
    ElMessage.success('角色配置已保存')
    roleCfgVisible.value = false
    load()
  } finally { saving.value = false }
}

function openGrantPerms(row) {
  grantKind.value = 'role'
  grantTarget.value = row
  grantTitle.value = `给「${row.roleName}」授权权限`
  grantHint.value = '选中的权限码会覆盖该角色当前权限集合'
  grantPlaceholder.value = '选择权限'
  grantOptions.value = perms.value.map((p) => ({
    value: String(p.id), label: `${p.permName}（${p.permCode}）`
  }))
  grantIds.value = []
  grantVisible.value = true
}

async function doGrant() {
  if (!grantIds.value.length) {
    ElMessage.warning('请至少选择一项'); return
  }
  saving.value = true
  try {
    if (grantKind.value === 'user') {
      await req.post(`/rbac/users/${grantTarget.value.id}/roles`,
        { ids: grantIds.value })
      ElMessage.success('角色已授予')
    } else {
      await req.post(`/rbac/roles/${grantTarget.value.id}/permissions`,
        { ids: grantIds.value })
      ElMessage.success('权限已授予')
    }
    grantVisible.value = false; load()
  } finally { saving.value = false }
}

onMounted(() => { loadOrgOptions(); load() })
</script>

<style scoped>
.perm-group { border: 1px solid #ebeef5; border-radius: 4px; margin-bottom: 8px; }
.perm-group-head { background: #fafafa; padding: 6px 10px; border-bottom: 1px solid #ebeef5; }
.perm-group-body { padding: 6px 12px 10px; }
/* 二级：资源；三级：操作，逐级缩进，便于看清层级 */
.perm-res { margin-top: 6px; }
.perm-res-head { padding-left: 20px; }
.perm-actions { padding-left: 46px; display: flex; flex-wrap: wrap; gap: 4px 18px; margin-top: 2px; }
</style>
