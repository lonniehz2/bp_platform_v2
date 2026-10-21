# -*- coding: utf-8 -*-
"""合同页接入同住人面板 + 空间页新增/删除"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'
V = FE + r'\views'

# ---------- 1) 合同页：加「同住人」按钮与抽屉 ----------
C = os.path.join(V, 'Contracts.vue')
s = io.open(C, encoding='utf-8').read()

if 'CohabitantPanel' not in s:
    # 操作列加按钮
    s = s.replace('''            <el-button link type="primary" @click="openSign(row)">签约</el-button>''',
                  '''            <el-button link type="primary" @click="openCohabitant(row)">同住人</el-button>
            <el-button link type="primary" @click="openSign(row)">签约</el-button>''', 1)

    # 加抽屉（在最后一个 el-dialog 结束前插入：用 </div> 前）
    s = s.replace('''    <!-- 终止 -->''',
                  '''    <!-- 同住人（保障人口） -->
    <el-drawer v-model="cohabitantVisible" title="同住人（保障人口）" size="620px">
      <CohabitantPanel :contract-id="cohabitantContractId" />
    </el-drawer>

    <!-- 终止 -->''', 1)

    # import + 状态 + 方法
    s = s.replace("import { contractApi } from '@/api/modules'",
                  "import { contractApi } from '@/api/modules'\n"
                  "import CohabitantPanel from '@/components/CohabitantPanel.vue'", 1)
    s = s.replace("const current = ref(null)",
                  "const current = ref(null)\n"
                  "const cohabitantVisible = ref(false)\n"
                  "const cohabitantContractId = ref(null)\n\n"
                  "function openCohabitant(row) {\n"
                  "  cohabitantContractId.value = row.id\n"
                  "  cohabitantVisible.value = true\n"
                  "}", 1)

    io.open(C, 'w', encoding='utf-8').write(s)
    print('  ✓ Contracts.vue 接入同住人面板')

# ---------- 2) 空间页：新增 + 删除 ----------
S = os.path.join(V, 'Spaces.vue')
t = io.open(S, encoding='utf-8').read()

if 'createVisible' not in t:
    # 工具栏加按钮
    t = t.replace('''      <el-button @click="expandAll = !expandAll">{{ expandAll ? '收起' : '展开' }}</el-button>''',
                  '''      <el-button @click="expandAll = !expandAll">{{ expandAll ? '收起' : '展开' }}</el-button>
      <el-button type="success" @click="openCreate">新增空间</el-button>''', 1)

    # 详情区加删除按钮
    t = t.replace('''        <pre v-if="current" class="raw">{{ JSON.stringify(current, null, 2) }}</pre>''',
                  '''        <div v-if="current" style="margin-top:12px">
          <el-button type="danger" size="small" @click="removeSpace">删除该空间</el-button>
          <span class="muted">（仅空节点可删；有下级或已挂房源会被拒绝）</span>
        </div>
        <DetailView v-if="current" :row="current" />''', 1)

    # 新增对话框
    t = t.replace('''    </el-row>
  </div>
</template>''',
                  '''    </el-row>

    <el-dialog v-model="createVisible" title="新增空间节点" width="560px">
      <el-form :model="f" label-width="120px">
        <el-form-item label="所属组织ID" required>
          <el-input v-model.number="f.orgId" /></el-form-item>
        <el-form-item label="上级节点">
          <el-input v-model.number="f.parentId"
                    placeholder="留空=顶级（只能是楼栋/片区）" /></el-form-item>
        <el-form-item label="空间编码" required>
          <el-input v-model="f.spaceCode" placeholder="同级唯一，建议用层级前缀" />
        </el-form-item>
        <el-form-item label="空间名称" required>
          <el-input v-model="f.spaceName" /></el-form-item>
        <el-form-item label="空间类型" required>
          <el-select v-model="f.spaceType" style="width:100%">
            <el-option label="片区 AREA" value="AREA" />
            <el-option label="楼栋 BUILDING" value="BUILDING" />
            <el-option label="单元 UNIT" value="UNIT" />
            <el-option label="楼层 FLOOR" value="FLOOR" />
            <el-option label="房间 ROOM" value="ROOM" />
            <el-option label="床位 BED" value="BED" />
            <el-option label="车位 PARKING" value="PARKING" />
            <el-option label="车库 GARAGE" value="GARAGE" />
            <el-option label="场地 SITE" value="SITE" />
          </el-select></el-form-item>
        <el-form-item label="面积(㎡)">
          <el-input-number v-model="f.area" :min="0" :precision="2"
                           style="width:100%" /></el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="f.sortNo" :min="1" style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="层级规则：顶级只能是楼栋或片区；单元挂楼栋、楼层挂单元、房间挂楼层" />
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>''', 1)

    # 脚本
    t = t.replace("import { spaceApi } from '@/api/modules'",
                  "import { spaceApi } from '@/api/modules'\n"
                  "import { ElMessage, ElMessageBox } from 'element-plus'\n"
                  "import DetailView from '@/components/DetailView.vue'", 1)
    t = t.replace("const treeRef = ref(null)",
                  "const treeRef = ref(null)\n"
                  "const createVisible = ref(false)\n"
                  "const saving = ref(false)\n"
                  "const f = reactive({ orgId: null, parentId: null, spaceCode: '',\n"
                  "  spaceName: '', spaceType: 'ROOM', area: null, sortNo: 1 })\n\n"
                  "function openCreate() {\n"
                  "  f.orgId = orgId.value\n"
                  "  f.parentId = current.value ? current.value.id : null\n"
                  "  createVisible.value = true\n"
                  "}\n\n"
                  "async function doCreate() {\n"
                  "  if (!f.orgId || !f.spaceCode || !f.spaceName) {\n"
                  "    ElMessage.warning('组织ID、编码、名称为必填')\n"
                  "    return\n"
                  "  }\n"
                  "  saving.value = true\n"
                  "  try {\n"
                  "    await spaceApi.create({ ...f })\n"
                  "    ElMessage.success('空间已创建')\n"
                  "    createVisible.value = false\n"
                  "    load()\n"
                  "  } finally { saving.value = false }\n"
                  "}\n\n"
                  "async function removeSpace() {\n"
                  "  await ElMessageBox.confirm(\n"
                  "    `确认删除空间「${current.value.spaceName}」？该操作不可恢复。`,\n"
                  "    '删除确认', { type: 'warning' })\n"
                  "  await spaceApi.remove(current.value.id)\n"
                  "  ElMessage.success('已删除')\n"
                  "  current.value = null\n"
                  "  load()\n"
                  "}", 1)

    # reactive 需要 import
    if 'import { ref, onMounted }' in t:
        t = t.replace('import { ref, onMounted }', 'import { ref, reactive, onMounted }', 1)
    elif 'import { ref, computed' in t:
        t = t.replace('import { ref, computed', 'import { ref, reactive, computed', 1)

    io.open(S, 'w', encoding='utf-8').write(t)
    print('  ✓ Spaces.vue 补新增/删除')

# ---------- 3) spaceApi 补 create/remove ----------
A = os.path.join(FE, 'api', 'modules.js')
a = io.open(A, encoding='utf-8').read()
if 'tree: (params) => req.get' in a and "spaceApi" in a:
    if "create: (data) => req.post('/spaces'" not in a:
        a = a.replace("  tree: (params) => req.get('/spaces/tree', { params })",
                      "  tree: (params) => req.get('/spaces/tree', { params }),\n"
                      "  create: (data) => req.post('/spaces', data),\n"
                      "  remove: (id) => req.delete(`/spaces/${id}`)", 1)
        io.open(A, 'w', encoding='utf-8').write(a)
        print('  ✓ spaceApi 补 create/remove')
else:
    print('  ! spaceApi 结构未匹配，需手工检查')
