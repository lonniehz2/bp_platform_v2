# -*- coding: utf-8 -*-
"""用户管理：补详情/编辑/启停/删除；授权角色弹窗预填已有角色。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'Rbac.vue')
s = io.open(V, encoding='utf-8').read()

# ---------- 1) 操作列 ----------
OLD_OPS = '''          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openGrantRoles(row)">授权角色</el-button>
            </template>
          </el-table-column>'''

NEW_OPS = '''          <el-table-column label="操作" width="300" fixed="right">
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
          </el-table-column>'''

if OLD_OPS in s:
    s = s.replace(OLD_OPS, NEW_OPS, 1)
    print('用户列表：已加操作按钮')

# ---------- 2) 授权角色预填 ----------
OLD_GRANT = '''function openGrantRoles(row) {
  grantKind.value = 'user'
  grantTarget.value = row
  grantTitle.value = `给「${row.realName || row.username}」授权角色`
  grantHint.value = '选中的角色会覆盖该用户当前角色集合'
  grantPlaceholder.value = '选择角色'
  grantOptions.value = roles.value.map((r) => ({
    value: String(r.id), label: `${r.roleName}（${r.roleCode}）`
  }))
  grantIds.value = []
  grantVisible.value = true
}'''

NEW_GRANT = '''async function openGrantRoles(row) {
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
}'''

if OLD_GRANT in s:
    s = s.replace(OLD_GRANT, NEW_GRANT, 1)
    print('授权角色：已预填已有角色')

# ---------- 3) 新增逻辑与弹窗 ----------
if 'openUserEdit' not in s.split('function openGrantRoles')[0]:
    ADD = '''
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
'''
    i = s.find('function openGrantRoles')
    s = s[:i] + ADD + '\n' + s[i:]
    print('用户管理：已加详情/编辑/启停/删除逻辑')

if 'title="用户详情"' not in s:
    DIALOG = '''
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
'''
    j = s.find('</template>')
    s = s[:j] + DIALOG + s[j:]
    print('用户管理：已加详情/编辑弹窗')

io.open(V, 'w', encoding='utf-8', newline='').write(s)
print('Rbac.vue 修改完成')
