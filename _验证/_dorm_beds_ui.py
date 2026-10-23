# -*- coding: utf-8 -*-
"""房源台账新增「床位管理」：选择房间 → 查看床位 → 批量生成床位。"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src',
                 'views', 'Houses.vue')
s = io.open(V, encoding='utf-8').read()

if 'bedVisible' in s:
    print('已存在')
    raise SystemExit(0)

anchor = '<el-button type="warning" plain @click="importVisible = true"'
if anchor not in s:
    raise SystemExit('未找到批量导入按钮')
s = s.replace(anchor, '''<el-button type="primary" plain @click="openBeds"
                   data-testid="house-beds">床位管理</el-button>
        ''' + anchor, 1)

dialog = '''
    <!-- 宿舍床位管理 -->
    <el-dialog v-model="bedVisible" title="宿舍床位管理" width="720px">
      <el-form label-width="90px">
        <el-form-item label="房间">
          <el-tree-select v-model="bedRoomId" :data="spaceTree" check-strictly
                          :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                          filterable placeholder="选择房间（ROOM）" style="width:100%"
                          @change="loadBeds" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8"><el-form-item label="生成数量">
            <el-input v-model="bedCount" type="number" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="床位月租">
            <el-input v-model="bedRent" type="number" /></el-form-item></el-col>
          <el-col :span="8"><el-form-item label="单床面积">
            <el-input v-model="bedArea" type="number" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <div style="margin:8px 0 12px">
        <el-button type="primary" :loading="saving" :disabled="!bedRoomId"
                   @click="doCreateBeds">批量生成床位</el-button>
        <span class="muted" style="font-size:12px;margin-left:8px">
          已存在的床位编号会自动跳过，不会重复创建
        </span>
      </div>
      <el-table :data="bedRows" size="small" border max-height="320" v-loading="bedLoading">
        <el-table-column prop="bedCode" label="床位编号" width="150" />
        <el-table-column prop="bedName" label="床位名称" min-width="150" />
        <el-table-column prop="houseStatus" label="房源状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.occupied ? 'success' : 'info'">
              {{ row.occupied ? '在租' : (row.houseStatus === 'VACANT' ? '空置' : row.houseStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="occupant" label="承租人" width="110">
          <template #default="{ row }">{{ row.occupant || '—' }}</template>
        </el-table-column>
        <el-table-column prop="leaseEnd" label="到期日" width="120">
          <template #default="{ row }">{{ row.leaseEnd || '—' }}</template>
        </el-table-column>
        <el-table-column prop="rentStandard" label="月租" width="100" />
      </el-table>
      <template #footer>
        <el-button @click="bedVisible = false">关闭</el-button>
      </template>
    </el-dialog>
'''
i = s.rfind('</template>')
s = s[:i] + dialog + s[i:]

script = '''
/** 宿舍床位管理 */
const bedVisible = ref(false)
const bedRoomId = ref('')
const bedRows = ref([])
const bedLoading = ref(false)
const bedCount = ref(4)
const bedRent = ref(300)
const bedArea = ref(8)
const spaceTree = ref([])

async function openBeds() {
  bedVisible.value = true
  bedRows.value = []
  bedRoomId.value = ''
  if (!spaceTree.value.length) {
    try {
      const orgId = query.orgId || auth.user?.orgId
      const tree = await req.get('/spaces/tree', { params: { orgId } })
      spaceTree.value = tree || []
    } catch (e) { /* 忽略，用户可手动输入房间 ID */ }
  }
}

async function loadBeds() {
  if (!bedRoomId.value) { bedRows.value = []; return }
  bedLoading.value = true
  try {
    bedRows.value = (await req.get('/houses/beds', {
      params: { roomSpaceId: bedRoomId.value } })) || []
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载床位失败')
  } finally { bedLoading.value = false }
}

async function doCreateBeds() {
  if (!bedRoomId.value) { ElMessage.warning('请选择房间'); return }
  saving.value = true
  try {
    const n = await req.post('/houses/beds/batch-create', {
      roomSpaceId: bedRoomId.value, count: Number(bedCount.value) || 1,
      rentStandard: Number(bedRent.value) || 0, areaPerBed: Number(bedArea.value) || 0
    })
    ElMessage.success(`已生成 ${n} 张床位`)
    await loadBeds()
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '生成失败')
  } finally { saving.value = false }
}
'''
a = s.find('onMounted(')
s = s[:a] + script + '\n' + s[a:]

if "import { useAuthStore }" not in s:
    s = s.replace("import req from '@/api/request'",
                  "import req from '@/api/request'\nimport { useAuthStore } from '@/store/auth'", 1)
if 'const auth = useAuthStore()' not in s:
    s = s.replace("const saving = ref(false)", "const saving = ref(false)\nconst auth = useAuthStore()", 1)

io.open(V, 'w', encoding='utf-8', newline='').write(s)
print('Houses.vue：床位管理已加')
