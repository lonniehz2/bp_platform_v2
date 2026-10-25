# -*- coding: utf-8 -*-
"""Rbac.vue：补上用户详情/编辑/启停/删除的脚本逻辑（上一轮只加了弹窗）。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'views', 'Rbac.vue')
s = io.open(V, encoding='utf-8').read()

if 'const userDetailVisible' in s:
    print('已存在用户管理逻辑')
    raise SystemExit(0)

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

anchor = '/** 组织下拉选项（新增用户时必填，决定数据归属） */'
if anchor in s:
    s = s.replace(anchor, ADD + anchor, 1)
    print('已插入用户管理逻辑')
else:
    print('未找到插入锚点')
    raise SystemExit(1)

# 确保 ElMessageBox 已导入
if 'ElMessageBox' in s and "ElMessageBox" not in s.split('import {')[1].split('}')[0]:
    s = s.replace("import { ElMessage } from 'element-plus'",
                  "import { ElMessage, ElMessageBox } from 'element-plus'", 1)
    print('已补 ElMessageBox 导入')

io.open(V, 'w', encoding='utf-8', newline='').write(s)
print('Rbac.vue 完成')
