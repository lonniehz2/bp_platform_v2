<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">房源台账</h3>
      <div class="spacer" />
      <el-input v-model="keyword" placeholder="房源编号/名称" clearable
                style="width:180px" @keyup.enter="reload" />
      <el-select v-model="houseStatus" placeholder="状态" clearable
                 style="width:140px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
      </el-select>
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="success" @click="openCreate">新增房源</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="houseCode" label="编号" width="150" />
      <el-table-column prop="houseName" label="名称" min-width="140" />
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
          <el-col :span="12"><el-form-item label="空间节点ID" required>
            <el-input v-model="f.spaceId" placeholder="房间级空间 ID" />
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
            <el-input v-model="f.orientation" /></el-form-item></el-col>
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
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { houseApi } from '@/api/modules'
import { enumLabel } from '@/constants/enums'
import DetailView from '@/components/DetailView.vue'

const statuses = ['VACANT', 'PENDING_ALLOC', 'ALLOCATED', 'OCCUPIED', 'LOCKED',
  'REPAIR', 'OFFLINE']
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const houseStatus = ref('')
const show = ref(false)
const detail = ref(null)
const createVisible = ref(false)
const f = reactive({ spaceId: null, houseCode: '', houseName: '',
  houseType: 'PUBLIC_RENTAL', structType: 'MULTI', useType: 'CIVIL',
  unitLayout: '', floorNo: 1, orientation: 'SOUTH', area: null, innerArea: null,
  decorateLevel: 'SIMPLE', rentStandard: null, rentUnit: 'AREA_MONTH',
  maxCapacity: 2 })

function statusType(s) {
  return s === 'OCCUPIED' || s === 'ALLOCATED' ? 'success'
    : (s === 'VACANT' ? 'info' : (s === 'REPAIR' ? 'warning' : 'danger'))
}

async function load() {
  loading.value = true
  try {
    const d = await houseApi.page({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined,
      houseStatus: houseStatus.value || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}
function reload() { pageNum.value = 1; load() }

function openCreate() { createVisible.value = true }
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
  houseStatus.value = ''
  keyword.value = ''
  pageNum.value = 1
  reload()
}

onMounted(load)
</script>
