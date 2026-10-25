# -*- coding: utf-8 -*-
"""前端修复：
1) 组织：树形展示编码/状态 + 列表加详情/编辑/启停/删除 + 编辑弹窗
2) 地址级联：label 字段映射修正
3) 审计日志枚举补齐（auditType / auditLevel IMPORTANT）
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views', 'Orgs.vue')
E = os.path.join(ROOT, 'frontend', 'src', 'constants', 'enums.js')

# ---------- 1) 地址级联：label 映射 ----------
s = io.open(V, encoding='utf-8').read()
if 'name: r.name' not in s:
    s = s.replace('''      resolve((list || []).map((r) => ({
        value: r.code, label: r.name, leaf: r.leaf
      })))''', '''      resolve((list || []).map((r) => ({
        code: r.code, name: r.name, leaf: r.leaf
      })))''')
    print('地址级联：返回字段改为 code/name（匹配 props 映射）')

# ---------- 2) 列表操作列 ----------
if 'label="操作"' not in s:
    s = s.replace('''            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                  {{ row.statusLabel || enumLabel('status', row.status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>''','''            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
                  {{ row.statusLabel || enumLabel('status', row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="openDetail(row)">详情</el-button>
                <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
                <el-button link :type="row.status === 'ENABLED' ? 'warning' : 'success'"
                           @click="toggleStatus(row)">
                  {{ row.status === 'ENABLED' ? '停用' : '启用' }}
                </el-button>
                <el-button link type="danger" @click="removeOrg(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>''')
    print('组织列表：已加操作列')

# ---------- 3) 树节点显示编码与状态 ----------
if 'treeLabel' not in s:
    s = s.replace("""<el-tree :data="tree" :props="{ label: 'orgName', children: 'children' }\"""",
                  """<el-tree :data="tree" :props="{ label: 'treeLabel', children: 'children' }\"""")
    print('组织树：改用 treeLabel（名称+编码+状态）')

# ---------- 4) 逻辑：详情/编辑/启停/删除 + 编辑弹窗 ----------
if 'function openEdit' not in s:
    ADD = '''
/** 详情 / 编辑 / 启停 / 删除 */
const detailVisible = ref(false)
const detailRow = ref({})
const editVisible = ref(false)
const editForm = reactive({ id: null, orgName: '', orgCode: '', orgType: '',
  parentId: null, community: '', address: '', sortNo: 1, remark: '' })

function openDetail(row) {
  detailRow.value = row
  detailVisible.value = true
}

function openEdit(row) {
  Object.assign(editForm, {
    id: row.id, orgName: row.orgName, orgCode: row.orgCode,
    orgType: row.orgType, parentId: row.parentId,
    community: row.community, address: row.address,
    sortNo: row.sortNo || 1, remark: row.remark
  })
  editVisible.value = true
}

async function saveEdit() {
  try {
    await req.put(`/orgs/${editForm.id}`, { ...editForm })
    ElMessage.success('已保存')
    editVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  }
}

async function toggleStatus(row) {
  const next = row.status === 'ENABLED' ? 'DISABLED' : 'ENABLED'
  try {
    await req.post(`/orgs/${row.id}/status`, { status: next })
    ElMessage.success(next === 'ENABLED' ? '已启用' : '已停用')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '操作失败')
  }
}

async function removeOrg(row) {
  try {
    await ElMessageBox.confirm(`确认删除组织「${row.orgName}」？`, '提示', { type: 'warning' })
    await req.delete(`/orgs/${row.id}`)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.message || '删除失败')
  }
}
'''
    i = s.find('function openCreate')
    s = s[:i] + ADD + '\n' + s[i:]
    print('组织页：已加详情/编辑/启停/删除逻辑')

# ---------- 5) 弹窗模板 ----------
if 'editVisible' in s and 'title="编辑组织"' not in s:
    DIALOG = '''
    <el-dialog v-model="detailVisible" title="组织详情" width="640px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="组织名称">{{ detailRow.orgName }}</el-descriptions-item>
        <el-descriptions-item label="编码">{{ detailRow.orgCode }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ enumLabel('orgType', detailRow.orgType) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ enumLabel('status', detailRow.status) }}</el-descriptions-item>
        <el-descriptions-item label="省">{{ detailRow.province || '—' }}</el-descriptions-item>
        <el-descriptions-item label="市">{{ detailRow.city || '—' }}</el-descriptions-item>
        <el-descriptions-item label="区县">{{ detailRow.district || '—' }}</el-descriptions-item>
        <el-descriptions-item label="街道">{{ detailRow.street || '—' }}</el-descriptions-item>
        <el-descriptions-item label="社区/村">{{ detailRow.community || '—' }}</el-descriptions-item>
        <el-descriptions-item label="详细地址" :span="2">{{ detailRow.address || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑组织" width="560px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="组织名称"><el-input v-model="editForm.orgName" /></el-form-item>
        <el-form-item label="编码"><el-input v-model="editForm.orgCode" /></el-form-item>
        <el-form-item label="社区/村"><el-input v-model="editForm.community" /></el-form-item>
        <el-form-item label="详细地址"><el-input v-model="editForm.address" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="editForm.sortNo" :min="1" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editForm.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
'''
    j = s.find('</template>')
    s = s[:j] + DIALOG + s[j:]
    print('组织页：已加详情/编辑弹窗')

io.open(V, 'w', encoding='utf-8', newline='').write(s)

# ---------- 6) 枚举补齐 ----------
t = io.open(E, encoding='utf-8').read()
if 'DATA:' not in t.split('auditLevel')[0]:
    t = t.replace('''  auditLevel: { INFO: '提示', WARNING: '警告', CRITICAL: '严重' },''',
'''  auditType: {
    DATA: '数据变更',
    SECURITY: '安全事件',
    CONFIG: '配置变更',
    LOGIN: '登录行为',
    FINANCE: '财务操作',
    SYSTEM: '系统操作'
  },
  auditLevel: {
    INFO: '提示',
    WARNING: '警告',
    IMPORTANT: '重要',
    CRITICAL: '严重'
  },''')
    io.open(E, 'w', encoding='utf-8', newline='').write(t)
    print('枚举：已补 auditType 与 auditLevel.IMPORTANT')
