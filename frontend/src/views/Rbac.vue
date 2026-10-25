<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">用户与权限</h3>
      <el-tag size="small" type="info">RBAC：用户 → 角色 → 权限</el-tag>
      <div class="spacer" />
      <el-button type="primary" @click="load">刷新</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon
              title="管理员（isAdmin=1）拥有全部权限；普通用户按角色授予的权限码访问接口与菜单"
              style="margin-bottom:12px" />

    <el-tabs v-model="tab">
      <!-- ================= 用户 ================= -->
      <el-tab-pane label="用户" name="user">
        <div class="toolbar">
          <el-button type="success" @click="userVisible = true">新增用户</el-button>
          <el-input v-model="ukeyword" placeholder="账号 / 姓名" clearable style="width:180px"
                    data-testid="rbac-user-keyword" @keyup.enter="load" />
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="resetUserQuery" data-testid="rbac-user-reset">清空</el-button>
          <span class="muted">共 {{ users.length }} 个</span>
        </div>
        <el-table :data="users" v-loading="loading" border size="small" max-height="460">
          <el-table-column prop="username" label="账号" width="140" />
          <el-table-column prop="realName" label="姓名" width="120" />
          <el-table-column label="角色" min-width="180">
            <template #default="{ row }">
              <span v-if="row.roleNames">{{ row.roleNames }}</span>
              <span v-else class="muted">未分配</span>
            
</template>
          </el-table-column>
          <el-table-column prop="orgId" label="组织" width="180">
            <template #default="{ row }">{{ row.orgIdName || row.orgId }}</template>


          </el-table-column>
          <el-table-column label="类型" width="110">
            <template #default="{ row }">{{ enumLabel('userType', row.userType) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('status', row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="管理员" width="90">
            <template #default="{ row }">
              <el-tag v-if="row.isAdmin == 1" size="small" type="danger">是</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openUserDetail(row)">详情</el-button>
              <el-button link type="primary" @click="openUserEdit(row)">编辑</el-button>
              <el-button link type="primary" @click="openGrantRoles(row)">授权角色</el-button>
              <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleUserStatus(row)">
                {{ row.status === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
              <el-button link type="danger" @click="removeUser(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 角色 ================= -->
      <el-tab-pane label="角色" name="role">
        <div class="toolbar">
          <el-button type="success" @click="roleVisible = true">新增角色</el-button>
          <el-input v-model="rkeyword" placeholder="角色编码 / 名称" clearable style="width:180px"
                    data-testid="rbac-role-keyword" @keyup.enter="load" />
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="resetRoleQuery" data-testid="rbac-role-reset">清空</el-button>
          <span class="muted">共 {{ roles.length }} 个</span>
        </div>
        <el-table :data="roles" v-loading="loading" border size="small" max-height="460">
          <el-table-column prop="roleCode" label="角色编码" width="170" />
          <el-table-column prop="roleName" label="角色名称" min-width="160" />
          <el-table-column label="数据范围" width="130">
            <template #default="{ row }">{{ enumLabel('dataScope', row.dataScope) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('status', row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRoleConfig(row)" data-testid="role-config">配置</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- ================= 权限 ================= -->
      <el-tab-pane label="权限" name="perm">
        <div class="toolbar">
          <el-button type="success" @click="permVisible = true">新增权限</el-button>
          <el-input v-model="pkeyword" placeholder="权限码 / 名称" clearable style="width:180px"
                    data-testid="rbac-perm-keyword" @keyup.enter="load" />
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="resetPermQuery" data-testid="rbac-perm-reset">清空</el-button>
          <span class="muted">共 {{ perms.length }} 个权限码</span>
        </div>
        <el-table :data="perms" v-loading="loading" border size="small" max-height="460">
          <el-table-column prop="permCode" label="权限码" width="240" />
          <el-table-column prop="permName" label="名称" min-width="150" />
          <el-table-column label="类型" width="110">
            <template #default="{ row }">{{ enumLabel('permType', row.permType) }}</template>
          </el-table-column>
          <el-table-column prop="routePath" label="路由" width="170" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('status', row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 新增用户 -->
    <el-dialog v-model="userVisible" title="新增用户" width="560px">
      <el-form :model="uf" label-width="110px">
        <el-form-item label="账号" required>
          <el-input v-model="uf.username" placeholder="登录名，唯一" /></el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="uf.password" type="password" show-password
                    placeholder="PBKDF2 加密存储" /></el-form-item>
        <el-form-item label="姓名" required>
          <el-input v-model="uf.realName" /></el-form-item>
        <el-form-item label="所属组织" required>
          <el-select v-model="uf.orgId" filterable clearable style="width:100%"
                     placeholder="选择组织（决定数据归属）" data-testid="user-org">
            <el-option v-for="o in orgOptions" :key="o.id"
                       :label="o.orgName" :value="String(o.id)" />
          </el-select></el-form-item>
        <el-form-item label="角色" required>
          <el-select v-model="uf.roleIds" multiple filterable style="width:100%"
                     placeholder="选择角色（决定该账号能看到什么、能做什么）"
                     data-testid="user-roles">
            <el-option v-for="r in roles" :key="r.id"
                       :label="`${r.roleName}（${r.roleCode}）`" :value="String(r.id)" />
          </el-select></el-form-item>
        <el-form-item label="绑定人员">
          <PersonPicker v-model="uf.personId" />
          <div class="muted" style="font-size:12px;line-height:1.5">
            角色数据范围为「仅本人」时（如租户），必须绑定人员档案，否则登录后看不到自己的数据
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增角色 -->
    <el-dialog v-model="roleVisible" title="新增角色" width="500px">
      <el-form :model="rf" label-width="110px">
        <el-form-item label="角色编码" required>
          <el-input v-model="rf.roleCode" placeholder="大写英文，如 REVIEWER" />
        </el-form-item>
        <el-form-item label="角色名称" required>
          <el-input v-model="rf.roleName" /></el-form-item>
        <el-form-item label="数据范围">
          <el-select v-model="rf.dataScope" style="width:100%">
            <el-option label="全部 ALL" value="ALL" />
            <el-option label="本部门 DEPT" value="DEPT" />
            <el-option label="仅本人 SELF" value="SELF" />
          </el-select></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateRole">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新增权限 -->
    <el-dialog v-model="permVisible" title="新增权限" width="560px">
      <el-form :model="pf" label-width="110px">
        <el-form-item label="权限码" required>
          <el-input v-model="pf.permCode" placeholder="如 fin:audit:view" /></el-form-item>
        <el-form-item label="权限名称" required>
          <el-input v-model="pf.permName" /></el-form-item>
        <el-form-item label="权限类型">
          <el-select v-model="pf.permType" style="width:100%">
            <el-option label="接口 API" value="API" />
            <el-option label="菜单 MENU" value="MENU" />
            <el-option label="按钮 BUTTON" value="BUTTON" />
            <el-option label="数据 DATA" value="DATA" />
          </el-select></el-form-item>
        <el-form-item label="路由路径">
          <el-input v-model="pf.routePath" placeholder="/xxx" /></el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="pf.sortNo" :min="1" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="permVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreatePerm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 角色配置：基本信息 + 数据范围 + 权限，一页完成 -->
    <el-dialog v-model="roleCfgVisible" :title="`配置角色：${roleCfg.roleName || ''}`" width="760px">
      <el-form :model="roleCfg" label-width="90px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="角色编码">
            <el-input :model-value="roleCfg.roleCode" disabled /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="角色名称">
            <el-input v-model="roleCfg.roleName" data-testid="role-cfg-name" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="数据范围">
            <el-select v-model="roleCfg.dataScope" style="width:100%" data-testid="role-cfg-scope">
              <el-option label="全部数据 ALL" value="ALL" />
              <el-option label="本组织 ORG" value="ORG" />
              <el-option label="本组织及下级 ORG_SUB" value="ORG_SUB" />
              <el-option label="仅本人 SELF" value="SELF" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="状态">
            <el-select v-model="roleCfg.status" style="width:100%">
              <el-option label="启用" value="ENABLED" />
              <el-option label="停用" value="DISABLED" />
            </el-select></el-form-item></el-col>
        </el-row>
      </el-form>

      <div class="toolbar" style="margin:4px 0 8px">
        <b>权限配置</b>
        <span class="muted">已选 {{ checkedPerms.length }} / {{ perms.length }}</span>
        <div class="spacer" />
        <el-button size="small" @click="checkAllPerms">全选</el-button>
        <el-button size="small" @click="checkedPerms = []">清空</el-button>
      </div>

      <el-tabs v-model="permTab" style="margin-top:4px">
        <el-tab-pane label="页面权限（菜单）" name="page">
          <div class="muted" style="margin-bottom:6px">
            控制该角色能看到哪些菜单与页面；勾选后对应菜单才会出现
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
        <el-tab-pane label="功能权限（操作）" name="func">
          <div class="muted" style="margin-bottom:6px">
            控制该角色能执行哪些操作（新增/修改/审核/导出等按钮级权限）
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
                  :label="p.permName"
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
        <el-button @click="roleCfgVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveRoleConfig">保存</el-button>
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
        <el-button @click="grantVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doGrant">保存</el-button>
      </template>
    </el-dialog>
  </div>
    <el-dialog v-model="userDetailVisible" title="用户详情" width="560px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="账号">{{ userDetail.username }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ userDetail.realName || '—' }}</el-descriptions-item>
        <el-descriptions-item label="手机">{{ userDetail.phone || '—' }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ userDetail.email || '—' }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ enumLabel('status', userDetail.status) }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ userDetail.userType || '—' }}</el-descriptions-item>
        <el-descriptions-item label="最近登录">{{ userDetail.lastLoginTime || '—' }}</el-descriptions-item>
        <el-descriptions-item label="登录次数">{{ userDetail.loginCount || 0 }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="userEditVisible" title="编辑用户" width="520px">
      <el-form :model="userForm" label-width="90px">
        <el-form-item label="姓名"><el-input v-model="userForm.realName" /></el-form-item>
        <el-form-item label="手机"><el-input v-model="userForm.phone" /></el-form-item>
        <el-form-item label="邮箱"><el-input v-model="userForm.email" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userEditVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'
import PersonPicker from '@/components/PersonPicker.vue'

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
    ElMessage.warning('账号、密码、姓名、所属组织为必填'); return
  }
  if (!(uf.roleIds && uf.roleIds.length)) {
    ElMessage.warning('请至少选择一个角色（角色决定该账号的权限）'); return
  }
  saving.value = true
  try {
    await req.post('/rbac/users', { ...uf, roleIds: uf.roleIds || [] })
    ElMessage.success('用户已创建')
    userVisible.value = false; load()
  } finally { saving.value = false }
}

async function doCreateRole() {
  if (!rf.roleCode || !rf.roleName) {
    ElMessage.warning('角色编码与名称为必填'); return
  }
  saving.value = true
  try {
    await req.post('/rbac/roles', { ...rf })
    ElMessage.success('角色已创建')
    roleVisible.value = false; load()
  } finally { saving.value = false }
}

async function doCreatePerm() {
  if (!pf.permCode || !pf.permName) {
    ElMessage.warning('权限码与名称为必填'); return
  }
  saving.value = true
  try {
    await req.post('/rbac/permissions', { ...pf })
    ElMessage.success('权限已创建')
    permVisible.value = false; load()
  } finally { saving.value = false }
}

/** 给用户授权角色 */
async function openGrantRoles(row) {
  grantKind.value = 'user'
  grantTarget.value = row
  grantTitle.value = `给「${row.realName || row.username}」授权角色`
  grantHint.value = '选中的角色会覆盖该用户当前角色集合'
  grantPlaceholder.value = '选择角色'
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
  rpt: '报表统计', open: '开放平台', gov: '监管报送', alloc: '配租轮候'
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
    open: '开放平台', webhook: 'Webhook', screen2: '大屏'
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
        byRes.get(res).push({ ...p, actionLabel: ACTION_LABEL[parts[2]] || parts[2] || '' })
      }
      const resources = Array.from(byRes.entries())
        .map(([rk, list]) => ({ key: rk, label: RES_LABEL[rk] || rk, items: list }))
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
