# -*- coding: utf-8 -*-
"""抄表：房源远程选择、批量列宽、导出组织/空间选择。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return s


p = os.path.join(V, 'MeterReadings.vue')

# 1) 单条录入：房源改远程搜索；无设备时明确提示
patch(p, [
    ('''        <el-form-item label="房源" required>
          <el-select v-model="rf.houseId" filterable style="width:100%" placeholder="选择房源"
                     @change="loadDevices">
            <el-option v-for="h in houses" :key="h.id" :value="h.id"
                       :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'" />
          </el-select>
        </el-form-item>''',
     '''        <el-form-item label="房源" required>
          <HouseSelect v-model="rf.houseId" width="100%" testid="meter-house"
                       @update:model-value="loadDevices" />
        </el-form-item>''', '单条房源'),
    ('''        <div class="muted" style="font-size:12px">未找到绑定设备，可手工选择设备或留空按人工录入</div>''',
     '''        <el-alert type="warning" :closable="false" style="margin-top:4px"
                  title="该房源在此计量项目下未绑定设备：可手工选择设备或留空按人工录入" />''', '无设备提示'),
])

# 2) 批量：房源远程、列宽、弹窗宽度
patch(p, [
    ('''    <el-dialog v-model="batchVisible" title="批量录入 / 导入抄表" width="920px">''',
     '''    <el-dialog v-model="batchVisible" title="批量录入 / 导入抄表" width="1180px">''', '批量宽度'),
    ('''        <el-table-column label="房源" width="230">
          <template #default="{ row }">
            <el-select v-model="row.houseId" filterable size="small" style="width:100%"
                       @change="fillRowDevice(row)">
              <el-option v-for="h in houses" :key="h.id" :value="h.id"
                         :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="计量项目" width="180">''',
     '''        <el-table-column label="房源" width="200">
          <template #default="{ row }">
            <HouseSelect v-model="row.houseId" width="100%"
                         @update:model-value="fillRowDevice(row)" />
          </template>
        </el-table-column>
        <el-table-column label="计量项目" width="150">''', '批量房源/项目列'),
    ('''        <el-table-column label="设备编号" width="180">''',
     '''        <el-table-column label="设备编号" width="160">''', '设备编号列宽'),
    ('''        <el-table-column prop="deviceName" label="设备名称" min-width="150" />''',
     '''        <el-table-column prop="deviceName" label="设备名称" width="170" />''', '设备名称列宽'),
    ('''        <el-table-column prop="deviceType" label="设备类型" width="120" />''',
     '''        <el-table-column prop="deviceType" label="设备类型" width="110" />''', '设备类型列宽'),
    ('''        <el-table-column label="读数" width="120">''',
     '''        <el-table-column label="读数" width="100">''', '读数列宽'),
    ('''        <el-table-column label="抄表日期" width="140">''',
     '''        <el-table-column label="抄表日期" width="135">''', '日期列宽'),
    ('''        <el-table-column label="" width="70">''',
     '''        <el-table-column label="" width="60">''', '删除列宽'),
])

# 3) 导出：组织/空间改为本地 el-select（不依赖组件挂载）
patch(p, [
    ('''        <el-form-item label="组织">
          <OrgSelect v-model="ex.orgId" width="100%" testid="meter-ex-org" />
        </el-form-item>
        <el-form-item label="空间">
          <SpaceSelect v-model="ex.spaceId" :org-id="ex.orgId" width="100%"
                       testid="meter-ex-space" placeholder="选择空间（含下级）" />
        </el-form-item>''',
     '''        <el-form-item label="组织">
          <el-select v-model="ex.orgId" filterable clearable style="width:100%"
                     placeholder="选择组织" @change="loadExportSpaces">
            <el-option v-for="o in exOrgs" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="空间">
          <el-select v-model="ex.spaceId" filterable clearable style="width:100%"
                     placeholder="选择空间（含下级），可空表示整个组织">
            <el-option v-for="s in exSpaces" :key="s.id" :label="s.label" :value="s.id" />
          </el-select>
        </el-form-item>''', '导出组织/空间'),
])

# 4) 脚本：导出组织/空间加载
s = io.open(p, encoding='utf-8').read()
if 'const exOrgs' not in s:
    s = s.replace('''const ex = reactive({ orgId: '', spaceId: '', feeItemId: '' })''',
                  '''const ex = reactive({ orgId: '', spaceId: '', feeItemId: '' })
const exOrgs = ref([])
const exSpaces = ref([])

async function loadExportOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    exOrgs.value = (d && d.rows) || []
  } catch (e) { exOrgs.value = [] }
}

function flattenSpaces(list, out) {
  (list || []).forEach((n) => {
    if (['ROOM', 'BED'].includes(n.spaceType)) {
      out.push({ id: n.id, label: n.fullName || n.spaceName })
    }
    if (n.children && n.children.length) flattenSpaces(n.children, out)
  })
}

async function loadExportSpaces() {
  ex.spaceId = ''
  exSpaces.value = []
  if (!ex.orgId) return
  try {
    const tree = await req.get('/spaces/tree', { params: { orgId: ex.orgId } })
    const out = []
    flattenSpaces(tree || [], out)
    exSpaces.value = out
  } catch (e) { exSpaces.value = [] }
}''', 1)
    s = s.replace('''function openExport() {
  ex.feeItemId = query.feeItemId || ''
  ex.orgId = ''
  ex.spaceId = ''
  exportVisible.value = true
}''', '''function openExport() {
  ex.feeItemId = query.feeItemId || ''
  ex.orgId = ''
  ex.spaceId = ''
  exSpaces.value = []
  exportVisible.value = true
  loadExportOrgs()
}''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 导出加载脚本')

# 5) 引入 HouseSelect
s = io.open(p, encoding='utf-8').read()
if 'HouseSelect' not in s:
    s = s.replace("import OrgSelect from '@/components/OrgSelect.vue'",
                  "import HouseSelect from '@/components/HouseSelect.vue'\n"
                  "import OrgSelect from '@/components/OrgSelect.vue'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ HouseSelect 导入')
