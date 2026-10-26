# -*- coding: utf-8 -*-
"""空间层级页：
  6) 支持编辑/删除
  7) 新增页组织、上级节点显示名称（下拉选择）
"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src')

# ---------- API ----------
P = os.path.join(V, 'api', 'modules.js')
s = io.open(P, encoding='utf-8').read()
if "update: (id, data) => req.put(`/spaces/${id}`" not in s:
    s = s.replace("""  create: (data) => req.post('/spaces', data),
  remove: (id) => req.delete(`/spaces/${id}`)""",
                  """  create: (data) => req.post('/spaces', data),
  update: (id, data) => req.put(`/spaces/${id}`, data),
  remove: (id) => req.delete(`/spaces/${id}`)""", 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('spaceApi 已加 update')

# ---------- 页面 ----------
P = os.path.join(V, 'views', 'Spaces.vue')
s = io.open(P, encoding='utf-8').read()

# 1) 详情面板加操作按钮
OLD_DETAIL = """        <el-empty v-else description="点击左侧节点查看详情" :image-size="60" />
        <DetailView :row="detail || current || row || {}" />"""
NEW_DETAIL = """        <el-empty v-else description="点击左侧节点查看详情" :image-size="60" />
        <div v-if="current" class="toolbar" style="margin:8px 0 12px">
          <el-button type="primary" plain @click="openEdit(current)">编辑</el-button>
          <el-button type="danger" plain @click="removeSpace">删除</el-button>
          <el-button plain @click="openCreateChild">在此节点下新增</el-button>
        </div>
        <DetailView :row="detail || current || row || {}" />"""
if OLD_DETAIL in s and 'openEdit' not in s:
    s = s.replace(OLD_DETAIL, NEW_DETAIL, 1)

# 2) 新增弹窗：组织/上级改为下拉
OLD_CREATE = """        <el-form-item label="所属组织ID" required>
          <el-input v-model="f.orgId" /></el-form-item>
        <el-form-item label="上级节点">
          <el-input v-model="f.parentId"
                    placeholder="留空=顶级（只能是楼栋/片区）" /></el-form-item>"""
NEW_CREATE = """        <el-form-item label="所属组织" required>
          <el-select v-model="f.orgId" filterable placeholder="选择组织（小区）"
                     style="width:100%" @change="onOrgChange">
            <el-option v-for="o in orgs" :key="o.id" :label="o.orgName" :value="o.id" />
          </el-select></el-form-item>
        <el-form-item label="上级节点">
          <el-tree-select v-model="f.parentId" :data="tree" check-strictly clearable
                          filterable :render-after-expand="false"
                          :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                          placeholder="留空=顶级（只能是楼栋/片区）" style="width:100%" />
        </el-form-item>"""
if OLD_CREATE in s:
    s = s.replace(OLD_CREATE, NEW_CREATE, 1)

# 3) 编辑弹窗（插在新增弹窗之后）
if 'editVisible' not in s:
    anchor = """    </el-dialog>
  </div>
</template>"""
    dlg = """    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑空间节点" width="520px">
      <el-form :model="ef" label-width="110px">
        <el-form-item label="所属组织">
          <span>{{ editOrgName || '—' }}</span>
        </el-form-item>
        <el-form-item label="上级节点">
          <span>{{ editParentName || '（顶级）' }}</span>
        </el-form-item>
        <el-form-item label="空间类型">
          <span>{{ enumLabel('spaceType', ef.spaceType) }}</span>
        </el-form-item>
        <el-form-item label="空间名称" required>
          <el-input v-model="ef.spaceName" />
        </el-form-item>
        <el-form-item label="空间编码" required>
          <el-input v-model="ef.spaceCode" />
        </el-form-item>
        <el-form-item label="面积(㎡)">
          <el-input-number v-model="ef.area" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="ef.sortNo" :min="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="ef.status" style="width:100%">
            <el-option label="启用" value="ENABLED" />
            <el-option label="停用" value="DISABLED" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="ef.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>"""
    s = s.replace(anchor, dlg, 1)

# 4) 脚本：编辑逻辑 + 组织切换 + 父级名称
if 'const editVisible' not in s:
    s = s.replace("""const createVisible = ref(false)""",
                  """const editVisible = ref(false)
const editOrgName = ref('')
const editParentName = ref('')
const ef = reactive({ id: null, spaceName: '', spaceCode: '', area: null,
  sortNo: 1, status: 'ENABLED', remark: '', spaceType: '' })

function openEdit(node) {
  Object.assign(ef, {
    id: node.id, spaceName: node.spaceName, spaceCode: node.spaceCode,
    area: node.area ? Number(node.area) : null, sortNo: node.sortNo || 1,
    status: node.status || 'ENABLED', remark: node.remark || '',
    spaceType: node.spaceType
  })
  editOrgName.value = node.orgIdName
    || (orgs.value.find((o) => String(o.id) === String(node.orgId)) || {}).orgName || ''
  editParentName.value = findNode(tree.value, node.parentId)?.spaceName || ''
  editVisible.value = true
}

async function doEdit() {
  if (!ef.spaceName || !ef.spaceCode) {
    ElMessage.warning('名称与编码为必填'); return
  }
  saving.value = true
  try {
    await spaceApi.update(ef.id, {
      spaceName: ef.spaceName, spaceCode: ef.spaceCode, area: ef.area,
      sortNo: ef.sortNo, status: ef.status, remark: ef.remark
    })
    ElMessage.success('已保存')
    editVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '保存失败')
  } finally { saving.value = false }
}

/** 在当前节点下新增子节点 */
function openCreateChild() {
  openCreate()
  f.parentId = current.value ? current.value.id : null
}

/** 切换组织后刷新空间树，供上级节点下拉使用 */
async function onOrgChange(id) {
  if (!id) return
  orgId.value = id
  await load()
}

const createVisible = ref(false)""", 1)

if 'function findNode' not in s:
    s = s.replace("""async function load() {""",
                  """function findNode(nodes, id) {
  if (!id) return null
  for (const n of nodes || []) {
    if (String(n.id) === String(id)) return n
    const sub = findNode(n.children, id)
    if (sub) return sub
  }
  return null
}

async function load() {""", 1)

# 5) 需要 enumLabel 导入
if "import { enumLabel }" not in s:
    s = s.replace("import { spaceApi, orgApi } from '@/api/modules'",
                  "import { spaceApi, orgApi } from '@/api/modules'\n"
                  "import { enumLabel } from '@/constants/enums'", 1)

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Spaces.vue 已加编辑/删除/名称下拉')
