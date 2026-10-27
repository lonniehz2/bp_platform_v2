<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">房源台账</h3>
      <div class="spacer" />
      <el-select v-model="orgFilter" placeholder="组织名称" clearable filterable
                 style="width:200px" data-testid="house-org-filter"
                 @change="reload">
        <el-option v-for="o in orgOptions" :key="o.id"
                   :label="o.orgName" :value="o.id" />
      </el-select>
      <el-input v-model="keyword" placeholder="房源编号/名称" clearable
                style="width:180px" @keyup.enter="reload" />
      <el-select v-model="houseStatus" placeholder="状态" clearable
                 style="width:140px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
      </el-select>
        <el-select v-model="houseTypeFilter" placeholder="业态" clearable
                   style="width:150px" @change="reload" data-testid="house-type-filter">
          <el-option v-for="t in houseTypes" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="openCreate">新增房源</el-button>
        <el-button type="primary" plain @click="openBeds"
                   data-testid="house-beds">床位管理</el-button>
        <el-button type="warning" plain @click="importVisible = true"
                   data-testid="house-import">批量导入</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="houseCode" label="编号" width="150" />
      <el-table-column prop="houseName" label="名称" min-width="140" />
      <el-table-column label="所属空间" width="170" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.spaceName">
                <el-tag v-if="row.spaceType === 'BED'" size="small" type="warning">床位</el-tag>
                {{ row.spaceName }}
              </span>
              <span v-else class="muted">—</span>
            </template>
          </el-table-column>
          <el-table-column label="类型" width="130">
        <template #default="{ row }">{{ row.houseTypeLabel || enumLabel('houseType', row.houseType) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="statusType(row.houseStatus)">
            {{ row.houseStatusLabel || enumLabel('houseStatus', row.houseStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="area" label="面积(㎡)" width="100" />
      <el-table-column label="租金标准" width="120">
        <template #default="{ row }">{{ row.rentStandard || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="changeStatus(row)">改状态</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <el-dialog v-model="createVisible" title="新增房源" width="640px">
      <el-form :model="f" label-width="120px">
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="所属组织">
            <el-select v-model="f.orgId" filterable clearable style="width:100%"
                       placeholder="选择组织后加载空间节点"
                       @change="onOrgChange">
              <el-option v-for="o in orgOptions" :key="o.id"
                         :label="o.orgName" :value="o.id" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="空间节点" required>
            <el-tree-select v-model="f.spaceId" :data="spaceTree" check-strictly
                            filterable :render-after-expand="false"
                            :props="{ label: 'spaceName', value: 'id', children: 'children' }"
                            placeholder="输入房间名搜索，如 1101室" style="width:100%"
                            @change="onSpacePicked" />
          </el-form-item></el-col>
          <el-col :span="12"><el-form-item label="房源编号" required>
            <el-input v-model="f.houseCode" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="房源名称" required>
            <el-input v-model="f.houseName" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="房源类型" required>
            <el-select v-model="f.houseType" style="width:100%">
              <el-option label="公租房" value="PUBLIC_RENTAL" />
              <el-option label="保障性租赁住房" value="AFFORDABLE_RENTAL" />
              <el-option label="人才公寓" value="TALENT" />
              <el-option label="公寓" value="APARTMENT" />
              <el-option label="宿舍" value="DORMITORY" />
              <el-option label="出租房" value="RENTAL" />
              <el-option label="酒店/民宿" value="HOTEL" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="建筑面积" required>
            <el-input-number v-model="f.area" :min="0.01" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="套内面积">
            <el-input-number v-model="f.innerArea" :min="0" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="建筑类型">
            <el-select v-model="f.structType" style="width:100%">
              <el-option label="多层" value="MULTI" />
              <el-option label="小高层" value="SMALL_HIGH" />
              <el-option label="高层" value="HIGH" />
              <el-option label="超高层" value="SUPER_HIGH" />
              <el-option label="别墅" value="VILLA" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="用途">
            <el-select v-model="f.useType" style="width:100%">
              <el-option label="民用" value="CIVIL" />
              <el-option label="商用" value="COMMERCIAL" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="户型">
            <el-input v-model="f.unitLayout" placeholder="如 2室1厅" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="楼层">
            <el-input-number v-model="f.floorNo" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="朝向">
            <el-select v-model="f.orientation" clearable style="width:100%"
                       placeholder="请选择朝向">
              <el-option v-for="o in ORIENTATIONS" :key="o.value" :label="o.label"
                         :value="o.value" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="装修标准">
            <el-select v-model="f.decorateLevel" style="width:100%">
              <el-option label="毛坯" value="ROUGH" />
              <el-option label="简装" value="SIMPLE" />
              <el-option label="精装" value="FINE" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="租金标准">
            <el-input-number v-model="f.rentStandard" :precision="2"
                             style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计价单位">
            <el-select v-model="f.rentUnit" style="width:100%">
              <el-option label="元/㎡·月" value="AREA_MONTH" />
              <el-option label="元/套·月" value="HOUSE_MONTH" />
              <el-option label="元/床·月" value="BED_MONTH" />
              <el-option label="元/套·夜" value="HOUSE_NIGHT" />
              <el-option label="元/床·夜" value="BED_NIGHT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="计量模式">
            <el-select v-model="f.meterMode" style="width:100%">
              <el-option label="独立表（每间独立计量）" value="INDEPENDENT" />
              <el-option label="整户分摊（一表按间分摊）" value="SHARED" />
              <el-option label="独立表 + 公区分摊" value="MIXED" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="最大入住">
            <el-input-number v-model="f.maxCapacity" :min="1" style="width:100%" />
          </el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="房源详情" size="560px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 批量导入房源（CSV 迁移用） -->
    <el-dialog v-model="importVisible" title="批量导入房源" width="620px">
      <el-alert type="info" :closable="false" show-icon
                title="CSV 列顺序：组织编码, 空间编码, 房源编号, 房源名称, 房源类型, 用途, 面积, 租金标准, 租金单位, 状态" />
      <div style="margin:12px 0;display:flex;gap:8px;align-items:center">
        <el-button size="small" @click="downloadTemplate">下载模板</el-button>
        <span class="muted" style="font-size:12px">
          首行可为表头；编号重复的行会被跳过并给出原因
        </span>
      </div>
      <el-upload :auto-upload="false" :limit="1" accept=".csv"
                 :on-change="onImportFile" :file-list="importFiles">
        <el-button type="primary" plain>选择 CSV 文件</el-button>
      </el-upload>
      <div v-if="importResult" style="margin-top:12px">
        <el-alert :type="importResult.skipped ? 'warning' : 'success'" :closable="false"
                  :title="`共 ${importResult.total} 行，成功 ${importResult.created}，跳过 ${importResult.skipped}`" />
        <el-table v-if="importResult.errors && importResult.errors.length"
                  :data="importResult.errors" size="small" border max-height="220"
                  style="margin-top:8px">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="原因" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="importVisible = false">关闭</el-button>
        <el-button type="primary" :loading="saving" :disabled="!importFiles.length"
                   @click="doImport">开始导入</el-button>
      </template>
    </el-dialog>

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
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button v-if="row.occupied" link type="primary"
                       @click="openSwapBed(row)">调换</el-button>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="bedVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 床位调换 -->
    <el-dialog v-model="swapVisible" title="床位调换" width="480px">
      <el-alert type="info" :closable="false" show-icon
                title="调换后原床位立即释放，合同租金与期限保持不变" />
      <el-form :model="swapForm" label-width="90px" style="margin-top:12px">
        <el-form-item label="当前床位">
          <span>{{ swapForm.fromBed }}（{{ swapForm.occupant }}）</span>
        </el-form-item>
        <el-form-item label="目标床位" required>
          <el-select v-model="swapForm.targetHouseId" style="width:100%"
                     placeholder="选择同房间的空床位">
            <el-option v-for="b in freeBeds" :key="b.houseId"
                       :label="b.bedName + '（月租 ' + (b.rentStandard || 0) + '）'"
                       :value="b.houseId" />
          </el-select>
        </el-form-item>
        <el-form-item label="调换原因">
          <el-input v-model="swapForm.reason" placeholder="如：室友调整、设备维修" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="swapVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSwapBed">确认调换</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { houseApi } from '@/api/modules'
import req from '@/api/request'
import { useAuthStore } from '@/store/auth'
import { enumLabel } from '@/constants/enums'
import DetailView from '@/components/DetailView.vue'

const statuses = ['VACANT', 'PENDING_ALLOC', 'ALLOCATED', 'OCCUPIED', 'LOCKED',
  'REPAIR', 'OFFLINE']
const loading = ref(false)
const saving = ref(false)
const auth = useAuthStore()
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const houseStatus = ref('')
const houseTypeFilter = ref('')
/** 多业态房源类型（宿舍/公寓/酒店民宿 与保障房并行） */
const houseTypes = [
  { value: 'PUBLIC_RENTAL', label: '公租房' },
  { value: 'AFFORDABLE_RENTAL', label: '经适房' },
  { value: 'TALENT', label: '人才房' },
  { value: 'APARTMENT', label: '公寓' },
  { value: 'DORMITORY', label: '宿舍' },
  { value: 'RENTAL', label: '租赁住房' },
  { value: 'HOTEL', label: '酒店/民宿' }
]
const show = ref(false)
const detail = ref(null)
const createVisible = ref(false)
const f = reactive({ spaceId: null, houseCode: '', houseName: '',
  houseType: 'PUBLIC_RENTAL', structType: 'MULTI', useType: 'CIVIL',
  unitLayout: '', floorNo: 1, orientation: 'SOUTH', area: null, innerArea: null,
  decorateLevel: 'SIMPLE', rentStandard: null, rentUnit: 'AREA_MONTH', meterMode: 'INDEPENDENT',
  maxCapacity: 2 })

function statusType(s) {
  return s === 'OCCUPIED' || s === 'ALLOCATED' ? 'success'
    : (s === 'VACANT' ? 'info' : (s === 'REPAIR' ? 'warning' : 'danger'))
}

const orgFilter = ref(null)

async function loadOrgFilterOptions() {
  if (orgOptions.value.length) return
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    orgOptions.value = d.rows || d || []
  } catch (e) { /* 忽略 */ }
}

async function load() {
  loading.value = true
  try {
    const d = await houseApi.page({
      pageNum: pageNum.value, pageSize: pageSize.value,
      orgId: orgFilter.value || undefined,
      keyword: keyword.value || undefined,
      houseStatus: houseStatus.value || undefined,
      houseType: houseTypeFilter.value || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

async function openCreate() {
  // 先确定组织：优先当前用户组织，否则取组织列表第一个；再加载该组织的空间树
  let orgId = f.orgId || auth.user?.orgId
  if (!orgOptions.value.length) {
    try {
      const od = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
      orgOptions.value = od.rows || od || []
    } catch (e) { /* 忽略 */ }
  }
  if (!orgId) {
    const first = orgOptions.value[0]
    orgId = first && first.id
  }
  if (orgId) {
    f.orgId = orgId
    await onOrgChange(orgId)
  }
  createVisible.value = true
}
async function doCreate() {
  if (!f.spaceId || !f.houseCode || !f.houseName || !f.area) {
    ElMessage.warning('空间节点、编号、名称、面积为必填'); return
  }
  saving.value = true
  try {
    await houseApi.create({ ...f })
    ElMessage.success('房源已创建')
    createVisible.value = false; reload()
  } finally { saving.value = false }
}

async function changeStatus(row) {
  const { value } = await ElMessageBox.prompt(
    '输入状态：VACANT / PENDING_ALLOC / ALLOCATED / OCCUPIED / LOCKED / REPAIR / OFFLINE',
    '变更房源状态', { inputValue: row.houseStatus || 'VACANT' })
  await houseApi.setStatus(row.id, { status: value })
  ElMessage.success('已更新'); load()
}

function resetQuery() {
  orgFilter.value = null
  houseStatus.value = ''
  houseTypeFilter.value = ''
  keyword.value = ''
  pageNum.value = 1
  reload()
}


/** 批量导入房源（CSV） */
const importVisible = ref(false)
const importFiles = ref([])
const importResult = ref(null)
let importFile = null

function onImportFile(file) {
  importFile = file.raw
  importFiles.value = [file]
  importResult.value = null
}

function downloadTemplate() {
  // 表头与示例值都用中文，业务人员可直接填；后端同时兼容英文码
  const header = '组织编码,空间编码,房源编号,房源名称,房源类型,用途,建筑面积(㎡),'
    + '租金标准,计价单位,房源状态\n'
  const note = '# 可选值：房源类型=公租房/保障性租赁住房/人才公寓/公寓/宿舍/酒店民宿/出租房；'
    + '用途=民用/商用；计价单位=元/㎡·月/元/套·月/元/床·月/元/套·夜/元/床·夜；'
    + '房源状态=空置/可租/待配租/已配租/已出租/维修中/锁定（本行可保留，导入时自动忽略）'
  const rows = [
    'DEMO-P1,P1-R1,HOUSE-001,示例房源1,公租房,民用,55,15,元/㎡·月,空置',
    'DEMO-P1,P1-R2,HOUSE-002,示例房源2,保障性租赁住房,民用,48.5,18.5,元/套·月,空置',
    'DEMO-P1,P1-R3,HOUSE-003,示例房源3,人才公寓,民用,32,1200,元/套·夜,待配租'
  ].join('\n')
  const blob = new Blob(['\ufeff' + header + '\n' + note + '\n' + rows + '\n'],
    { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '房源导入模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

async function doImport() {
  if (!importFile) { ElMessage.warning('请选择 CSV 文件'); return }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('file', importFile)
    const r = await req.post('/houses/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    importResult.value = r || {}
    ElMessage.success(`导入完成：成功 ${r?.created || 0}，跳过 ${r?.skipped || 0}`)
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导入失败')
  } finally { saving.value = false }
}


/** 宿舍床位管理 */
const bedVisible = ref(false)
const bedRoomId = ref('')
const bedRows = ref([])
const bedLoading = ref(false)
const bedCount = ref(4)
const bedRent = ref(300)
const bedArea = ref(8)
const spaceTree = ref([])

/** 朝向：与后端枚举一致（EnumLabels 已配中文） */
const ORIENTATIONS = [
  { value: 'SOUTH', label: '朝南' },
  { value: 'NORTH', label: '朝北' },
  { value: 'EAST', label: '朝东' },
  { value: 'WEST', label: '朝西' },
  { value: 'SOUTHEAST', label: '东南' },
  { value: 'SOUTHWEST', label: '西南' },
  { value: 'NORTHEAST', label: '东北' },
  { value: 'NORTHWEST', label: '西北' },
  { value: 'NORTH_SOUTH', label: '南北通透' }
]

async function openBeds() {
  bedVisible.value = true
  bedRows.value = []
  bedRoomId.value = ''
  await ensureSpaceTree()
}

/**
 * 确保空间树可用。
 * 后端 /spaces/tree 必须带 orgId；账号无 orgId 时回退到第一个可选组织，
 * 否则房间下拉会是空白（本次修复点）。
 */
const orgOptions = ref([])

/** 组织变化时重新加载空间树 */
async function onOrgChange(orgId) {
  spaceTree.value = []
  if (!orgId) return
  try {
    const tree = await req.get('/spaces/tree', { params: { orgId } })
    spaceTree.value = tree || []
    if (!spaceTree.value.length) {
      ElMessage.warning('该组织下暂无空间节点，请先在「空间管理」创建楼栋/单元/房间')
    }
  } catch (e) {
    ElMessage.error('空间树加载失败：' + (e?.response?.data?.message || e?.message || e))
  }
}

async function ensureSpaceTree() {
  if (spaceTree.value.length) return spaceTree.value
  let orgId = auth.user?.orgId
  if (!orgId) {
    try {
      const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
      const list = d.rows || d || []
      const first = list[0]
      orgId = first && first.id
    } catch (e) { /* 忽略 */ }
  }
  if (!orgId) return []
  try {
    if (!orgOptions.value.length) {
      const od = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
      orgOptions.value = od.rows || od || []
    }
    if (!f.orgId) f.orgId = orgId
    const tree = await req.get('/spaces/tree', { params: { orgId } })
    spaceTree.value = tree || []
  } catch (e) {
    ElMessage.error('空间树加载失败：' + (e?.response?.data?.message || e?.message || e))
  }
  return spaceTree.value
}

/** 选中房间后自动带出组织/房号，减少手填 */
function onSpacePicked(id) {
  const hit = findNode(spaceTree.value, id)
  if (!hit) return
  if (!f.houseName) f.houseName = hit.spaceName
  if (!f.houseCode) f.houseCode = hit.spaceCode
  if (!f.orgId && hit.orgId) f.orgId = hit.orgId
  if (!f.area && hit.area) f.area = Number(hit.area)
}

function findNode(nodes, id) {
  for (const n of nodes || []) {
    if (String(n.id) === String(id)) return n
    const sub = findNode(n.children, id)
    if (sub) return sub
  }
  return null
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


/** 床位调换 */
const swapVisible = ref(false)
const swapForm = reactive({ contractId: '', fromBed: '', occupant: '',
  targetHouseId: '', reason: '' })
const freeBeds = computed(() =>
  bedRows.value.filter((b) => !b.occupied && b.houseId))

function openSwapBed(row) {
  if (!row.contractNo) {
    ElMessage.warning('该床位缺少合同信息，无法调换')
    return
  }
  Object.assign(swapForm, { contractId: '', fromBed: row.bedName,
    occupant: row.occupant || '', targetHouseId: '', reason: '' })
  // 用合同号反查合同 ID 由后端承担；此处通过合同列表接口拿 ID
  req.get('/contracts', { params: { pageNum: 1, pageSize: 50, keyword: row.contractNo } })
    .then((res) => {
      const list = (res && res.rows) || []
      const hit = list.find((c) => c.contractNo === row.contractNo)
      if (!hit) { ElMessage.warning('未找到对应合同'); return }
      swapForm.contractId = hit.id
      swapVisible.value = true
    })
    .catch(() => ElMessage.error('查询合同失败'))
}

async function doSwapBed() {
  if (!swapForm.targetHouseId) { ElMessage.warning('请选择目标床位'); return }
  saving.value = true
  try {
    await req.post(`/contracts/${swapForm.contractId}/swap-bed`, {
      targetHouseId: swapForm.targetHouseId, reason: swapForm.reason
    })
    ElMessage.success('床位已调换')
    swapVisible.value = false
    await loadBeds()
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '调换失败')
  } finally { saving.value = false }
}

onMounted(() => { load(); loadOrgFilterOptions() })
</script>
