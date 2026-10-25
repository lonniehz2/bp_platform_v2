# -*- coding: utf-8 -*-
"""前端：角色 / 权限 / 数据字典 / 开放平台 增加启用停用入口。

注意：只加按钮与函数，不新增弹窗（避免弹窗写进表格插槽导致遮罩叠加）。
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.path.join(HERE, '..', 'frontend', 'src', 'views')


def add_toggle(path, table_anchor, new_column, func_anchor, new_funcs,
               already_marker):
    s = io.open(path, encoding='utf-8').read()
    if already_marker in s:
        print(os.path.basename(path) + '：已存在')
        return
    if table_anchor not in s:
        print(os.path.basename(path) + '：找不到表格锚点')
        return
    s = s.replace(table_anchor, table_anchor + new_column, 1)
    if func_anchor not in s:
        print(os.path.basename(path) + '：找不到函数锚点')
        return
    s = s.replace(func_anchor, new_funcs + '\n' + func_anchor, 1)
    io.open(path, 'w', encoding='utf-8', newline='').write(s)
    print(os.path.basename(path) + '：已加状态切换')


# ---------------- 1) 角色 ----------------
ROLE_COL = '''          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRoleConfig(row)" data-testid="role-config">配置</el-button>
            </template>
          </el-table-column>'''

ROLE_COL_NEW = '''          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openRoleConfig(row)" data-testid="role-config">配置</el-button>
              <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleRoleStatus(row)">
                {{ row.status === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>'''

ROLE_FUNCS = '''
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

'''

P = os.path.join(V, 'Rbac.vue')
s = io.open(P, encoding='utf-8').read()
if 'toggleRoleStatus' not in s:
    s = s.replace(ROLE_COL, ROLE_COL_NEW, 1)
    # 权限表加操作列
    PERM_TABLE_END = '''          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('status', row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>'''
    PERM_TABLE_END_NEW = '''          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                {{ enumLabel('status', row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                         @click="togglePermStatus(row)">
                {{ row.status === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>'''
    s = s.replace(PERM_TABLE_END, PERM_TABLE_END_NEW, 1)

    FUNCS = ROLE_FUNCS + '''
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

'''
    anchor = 'function openRoleConfig'
    if anchor in s:
        s = s.replace(anchor, FUNCS + anchor, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('Rbac.vue：角色/权限已加状态切换')

# ---------------- 2) 数据字典 ----------------
P = os.path.join(V, 'SysAdmin.vue')
s = io.open(P, encoding='utf-8').read()
if 'toggleDictStatus' not in s:
    DICT_OLD = '''          <el-table-column prop="dictStatus" label="状态" width="110">
            <template #default="{ row }">{{ row.dictStatusLabel || enumLabel('dictStatus', row.dictStatus) }}</template>
          </el-table-column>
        </el-table>'''
    DICT_NEW = '''          <el-table-column prop="dictStatus" label="状态" width="110">
            <template #default="{ row }">{{ row.dictStatusLabel || enumLabel('dictStatus', row.dictStatus) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button link :type="row.dictStatus === 'ENABLED' ? 'warning' : 'success'"
                         @click="toggleDictStatus(row)">
                {{ row.dictStatus === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>'''
    if DICT_OLD in s:
        s = s.replace(DICT_OLD, DICT_NEW, 1)
        FUNC = '''
/** 字典项启用 / 停用 */
async function toggleDictStatus(row) {
  const next = row.dictStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.post(`/sys/dicts/${row.id}/status`, { status: next })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    loadDict()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

'''
        anchor = 'async function loadDict'
        if anchor in s:
            s = s.replace(anchor, FUNC + anchor, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('SysAdmin.vue：数据字典已加状态切换')
    else:
        print('SysAdmin.vue：找不到字典表锚点')

# ---------------- 3) 开放平台 ----------------
P = os.path.join(V, 'OpenApps.vue')
s = io.open(P, encoding='utf-8').read()
if 'toggleAppStatus' not in s:
    OPS_OLD = '''          <el-button link type="warning" @click="resetSecret(row)">重置密钥</el-button>
          <el-button link @click="openDetail(row)">详情</el-button>'''
    OPS_NEW = '''          <el-button link type="warning" @click="resetSecret(row)">重置密钥</el-button>
          <el-button link @click="openDetail(row)">详情</el-button>
          <el-button link :type="row.appStatus === 'ENABLED' ? 'warning' : 'success'"
                     @click="toggleAppStatus(row)">
            {{ row.appStatus === 'ENABLED' ? '停用' : '启用' }}
          </el-button>'''
    if OPS_OLD in s:
        s = s.replace(OPS_OLD, OPS_NEW, 1)
        s = s.replace(':width="ROWACTIONS ? 210 : 110"', ':width="ROWACTIONS ? 300 : 250"', 1)
        FUNC = '''
/** 应用启用 / 停用 */
async function toggleAppStatus(row) {
  const next = row.appStatus === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.post(`/open/apps/${row.id}/status`, { status: next })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

'''
        anchor = 'function openDetail'
        if anchor in s:
            s = s.replace(anchor, FUNC + anchor, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('OpenApps.vue：已加应用状态切换')
    else:
        print('OpenApps.vue：找不到操作列锚点')
