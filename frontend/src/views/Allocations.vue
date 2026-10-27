<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">配租批次</h3>
        <el-button type="success" @click="openBatchCreate" data-testid="batch-create">新建批次</el-button>
        <div class="spacer" />
        <el-input v-model="seed" placeholder="摇号种子（可复现）" style="width:200px" />
        <el-button type="primary" @click="load">刷新</el-button>
      </div>

      <FilterBar @search="load" @reset="resetQuery">
        <el-select v-model="af.status" placeholder="批次状态" clearable style="width:160px"
                   data-testid="alloc-status">
          <el-option label="草稿" value="DRAFT" />
          <el-option label="已发布" value="PUBLISHED" />
          <el-option label="报名中" value="SIGNUP" />
          <el-option label="摇号中" value="LOTTERY" />
          <el-option label="摇号完成" value="LOTTERY_DONE" />
          <el-option label="选房中" value="SELECTING" />
          <el-option label="已配租" value="ALLOCATED" />
          <el-option label="已结束" value="CLOSED" />
          <el-option label="已取消" value="CANCELLED" />
        </el-select>
        <el-select v-model="af.orgId" placeholder="组织名称" clearable filterable
                   style="width:220px" data-testid="alloc-org">
          <el-option v-for="o in orgOptions" :key="o.id"
                     :label="o.orgName" :value="o.id" />
        </el-select>
      </FilterBar>

      <el-table :data="batches" v-loading="loading" border size="small">
        <el-table-column prop="id" label="批次ID" width="140" />
        <el-table-column prop="batchNo" label="批次号" width="160" />
        <el-table-column prop="batchName" label="名称" />
        <el-table-column label="组织" width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.orgIdName || orgNameOf(row.orgId) }}</template>
        </el-table-column>
        <el-table-column prop="batchStatus" label="状态" width="110">
          <template #default="{ row }">{{ row.batchStatusLabel || enumLabel('batchStatus', row.batchStatus) }}</template>
        </el-table-column>
        <el-table-column prop="houseCount" label="房源数" width="90" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
            <el-button link type="primary" @click="openAddHouses(row)" data-testid="batch-add-house">加房源</el-button>
            <el-button v-if="row.batchStatus === 'DRAFT'" link type="success"
                       @click="doTransition(row, 'PUBLISHED')"
                       data-testid="batch-publish">发布</el-button>
            <el-button v-if="row.batchStatus === 'PUBLISHED'" link type="primary"
                       @click="doTransition(row, 'SIGNUP')"
                       data-testid="batch-signup">开始报名</el-button>
            <el-button v-if="row.batchStatus === 'SIGNUP'" link type="warning"
                       @click="doTransition(row, 'LOTTERY')"
                       data-testid="batch-to-lottery">结束报名</el-button>
            <el-button v-if="['DRAFT','PUBLISHED','SIGNUP'].includes(row.batchStatus)"
                       link type="danger" @click="doTransition(row, 'CANCELLED')">取消</el-button>
            <el-button link type="primary" @click="runLottery(row)">摇号</el-button>
            <el-button link @click="viewResults(row)">结果</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="page-card">
      <h3 style="margin:0 0 12px">配租单</h3>
      <el-table :data="allocations" v-loading="loading" border size="small">
        <el-table-column prop="allocationNo" label="配租单号" width="170" />
        <el-table-column prop="personId" label="人员" width="110">
          <template #default="{ row }">{{ row.personName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="houseId" label="房源" width="110">
          <template #default="{ row }">{{ row.houseIdName || row.houseId }}</template>
        </el-table-column>
        <el-table-column prop="allocationStatusLabel" label="状态" width="110" />
        <el-table-column prop="lockRemainHours" label="锁定剩余(小时)" width="130" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" :disabled="!!row.lockOverdue"
                       @click="sign(row)">签约</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="resultVisible" title="摇号结果" width="700px">
      <el-alert type="info" :closable="false" show-icon
                title="中签数 = 房源数；中签之后 3 名为递补。相同种子可完全复现，可用于公证复核。" />
      <el-table :data="results" border size="small" style="margin-top:12px">
        <el-table-column prop="waitingId" label="轮候单" width="140">
          <template #default="{ row }">{{ row.waitingId }}</template>
        </el-table-column>
        <el-table-column prop="personId" label="人员" width="120">
          <template #default="{ row }">{{ row.personName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="totalScore" label="总分" width="100" />
        <el-table-column prop="selectSeq" label="选房序号" width="90" />
        <el-table-column prop="resultType" label="结果" width="100">
          <template #default="{ row }">{{ row.resultTypeLabel || enumLabel('resultType', row.resultType) }}</template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" title="详情" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>

    <!-- 新建批次 -->
    <el-dialog v-model="batchCreateVisible" title="新建配租批次" width="620px">
      <el-form :model="bf" label-width="110px">
        <el-form-item label="批次名称" required>
          <el-input v-model="bf.batchName" placeholder="如：2026 年第一批公租房配租" />
        </el-form-item>
        <el-form-item label="项目组织" required>
          <el-select v-model="bf.orgId" filterable style="width:100%"
                     placeholder="选择所属小区/项目">
            <el-option v-for="o in batchOrgs" :key="o.id" :label="o.orgName" :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="保障类型" required>
            <el-select v-model="bf.securityType" style="width:100%">
              <el-option label="公租房" value="PUBLIC" />
              <el-option label="经适房" value="AFFORDABLE" />
              <el-option label="人才房" value="TALENT" />
              <el-option label="廉租房" value="LOW_RENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="批次类型" required>
            <el-select v-model="bf.batchType" style="width:100%">
              <el-option label="摇号配租" value="LOTTERY" />
              <el-option label="选房配租" value="SELECT" />
              <el-option label="直接配租" value="DIRECT" />
              <el-option label="补充配租" value="SUPPLEMENT" />
            </el-select></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="报名开始">
            <el-date-picker v-model="bf.signupStart" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="报名结束">
            <el-date-picker v-model="bf.signupEnd" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="摇号时间">
            <el-date-picker v-model="bf.lotteryTime" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="24"><el-form-item label="房源">
            <div style="width:100%">
              <el-select v-model="bf.houseIds" multiple filterable remote
                         :remote-method="searchHouses" :loading="houseLoading"
                         placeholder="选择组织后搜索待分配房源（可多选）" style="width:100%">
                <el-option v-for="h in houseOptions" :key="h.id"
                           :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'"
                           :value="h.id" />
              </el-select>
              <div class="muted" style="font-size:12px;margin-top:4px">
                已选 {{ (bf.houseIds || []).length }} 套；仅显示所选组织下「待分配」房源
              </div>
            </div>
          </el-form-item></el-col>
          <el-col :span="24"><el-form-item label="公证信息">
            <el-input v-model="bf.notaryInfo" placeholder="可空，如公证处与公证号" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="batchCreateVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateBatch">创建</el-button>
      </template>
    </el-dialog>

    <!-- 批次加房源 -->
    <el-dialog v-model="addHouseVisible" :title="`向批次「${addHouseBatch?.batchName || ''}」加入房源`"
               width="560px">
      <el-alert type="info" :closable="false" show-icon
                title="输入房源 ID，多个用英文逗号分隔；房源需为「空置可租」状态" />
      <el-input v-model="houseIdsText" type="textarea" :rows="4" style="margin-top:10px"
                placeholder="1000000000000012161,1000000000000012159" />
      <template #footer>
        <el-button @click="addHouseVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doAddHouses">加入</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
/** 通用详情弹窗（复用 DetailView） */
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted, watch } from 'vue'
import DetailView from '@/components/DetailView.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { allocationApi } from '@/api/modules'
import req from '@/api/request'
import FilterBar from '@/components/FilterBar.vue'

const loading = ref(false)
const batches = ref([])
const allocations = ref([])
const results = ref([])
const resultVisible = ref(false)
const seed = ref('20261019')
/** 批次筛选（后端 /allocations/batches 支持 status / orgId） */
const af = reactive({ status: '', orgId: '' })

/** 清空筛选条件 */
function resetQuery() {
  af.status = ''
  af.orgId = ''
  load()
}

async function load() {
  loading.value = true
  try {
    const b = await allocationApi.batches({
      pageNum: 1, pageSize: 50,
      status: af.status || undefined,
      orgId: af.orgId || undefined
    })
    batches.value = b.rows || []
    const a = await allocationApi.allocations({ pageNum: 1, pageSize: 50 })
    allocations.value = a.rows || []
  } finally {
    loading.value = false
  }
}

async function runLottery(row) {
  const [waiting, houses] = await Promise.all([
    waitingCountOf(row.securityType),
    batchHouseCount(row.id)
  ])
  if (!waiting) {
    ElMessage.warning('当前轮候池中没有该保障类型的待配租人员，无法摇号')
    return
  }
  if (!houses) {
    ElMessage.warning('本批次还没有房源，请先「加房源」')
    return
  }
  try {
    await ElMessageBox.confirm(
      `本次将对 ${waiting} 名轮候人员与 ${houses} 套房源执行摇号（报名即轮候）。\n`
      + '摇号结果生成后可在「结果」中查看，并用于公示。',
      '确认摇号',
      { type: 'warning', confirmButtonText: '开始摇号', cancelButtonText: '取消' })
  } catch (e) { return }
  try {
    await req.post('/allocation/lottery', { batchId: row.id, seed: seed.value || undefined })
    ElMessage.success('摇号完成')
    load()
    viewResults(row)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '摇号失败')
  }
}

async function viewResults(row) {
  results.value = await allocationApi.results(row.id)
  resultVisible.value = true
}

async function sign(row) {
  await ElMessageBox.confirm(
    '签约前系统会校验配租公示是否已完成（≥7 自然日且已结束）。确认继续？',
    '签约确认', { type: 'warning' })
  try {
    await allocationApi.sign(row.id, {})
    ElMessage.success('签约成功')
    load()
  } catch (e) {
    // 拦截器已提示（常见：公示未结束）
  }
}


/** 新建批次 / 批次加房源（此前只能看列表，无法从界面建批次） */
const batchCreateVisible = ref(false)
const addHouseVisible = ref(false)
const addHouseBatch = ref(null)
const houseIdsText = ref('')
const bf = reactive({ batchName: '', orgId: '', houseIds: [], securityType: 'PUBLIC',
  batchType: 'LOTTERY', signupStart: '', signupEnd: '', lotteryTime: '',
  notaryInfo: '' })
const orgOptions = ref([])
const batchOrgs = ref([])


/** 组织列表（名称用于筛选与批次下拉） */
async function loadOrgOptions() {
  if (orgOptions.value.length) return
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    const rows = (d && d.rows) || (Array.isArray(d) ? d : [])
    orgOptions.value = rows.map((o) => ({ id: o.id, orgName: o.orgName }))
  } catch (e) { /* 忽略 */ }
}

function orgNameOf(id) {
  const hit = orgOptions.value.find((o) => String(o.id) === String(id))
  return hit ? hit.orgName : (id || '—')
}

const houseOptions = ref([])
const houseLoading = ref(false)

/** 组织下「待分配」房源，支持关键字搜索 */
async function searchHouses(keyword) {
  if (!bf.orgId) return
  houseLoading.value = true
  try {
    const d = await req.get('/houses', {
      params: { pageNum: 1, pageSize: 100, orgId: bf.orgId,
        houseStatus: 'PENDING_ALLOC', keyword: keyword || undefined }
    })
    houseOptions.value = (d && d.rows) || []
  } catch (e) { houseOptions.value = [] } finally { houseLoading.value = false }
}

async function openBatchCreate() {
  Object.assign(bf, { batchName: '', orgId: '', houseIds: [], securityType: 'PUBLIC',
    batchType: 'LOTTERY', signupStart: '', signupEnd: '', lotteryTime: '', notaryInfo: '' })
  houseOptions.value = []
  batchCreateVisible.value = true
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 200 } })
    const rows = (d && d.rows) || (Array.isArray(d) ? d : [])
    batchOrgs.value = rows.map((o) => ({ id: String(o.id), orgName: o.orgName }))
    if (!orgOptions.value.length) orgOptions.value = batchOrgs.value
  } catch (e) { batchOrgs.value = [] }
  if (!bf.orgId && batchOrgs.value.length) {
    bf.orgId = batchOrgs.value[0].id
    searchHouses('')
  }
}

async function doCreateBatch() {
  if (!bf.batchName) { ElMessage.warning('请填写批次名称'); return }
  if (!bf.orgId) { ElMessage.warning('请选择项目组织'); return }
  const ids = (bf.houseIds || []).map(String)
  saving.value = true
  try {
    await req.post('/allocation/batches', {
      batchName: bf.batchName,
      orgId: bf.orgId,
      securityType: bf.securityType,
      batchType: bf.batchType,
      signupStart: bf.signupStart || null,
      signupEnd: bf.signupEnd || null,
      lotteryTime: bf.lotteryTime || null,
      houseIds: ids.length ? ids : null,
      notaryInfo: bf.notaryInfo || null
    })
    ElMessage.success('批次已创建')
    batchCreateVisible.value = false
    load()
  } finally { saving.value = false }
}

function openAddHouses(row) {
  addHouseBatch.value = row
  houseIdsText.value = ''
  addHouseVisible.value = true
}

async function doAddHouses() {
  const ids = houseIdsText.value.split(/[,，\s]+/).map((x) => x.trim()).filter(Boolean)
  if (!ids.length) { ElMessage.warning('请填写房源 ID'); return }
  saving.value = true
  try {
    await req.post(`/allocation/batches/${addHouseBatch.value.id}/houses`, { houseIds: ids })
    ElMessage.success(`已加入 ${ids.length} 个房源`)
    addHouseVisible.value = false
    load()
  } finally { saving.value = false }
}


/** 批次状态流转：发布 → 报名 → 摇号 */
const TRANSITION_TIP = {
  PUBLISHED: '发布后批次对外可见，可进入报名阶段',
  SIGNUP: '开始报名后，本批次按「报名即轮候」处理：该保障类型的轮候人员自动参与本批次摇号',
  LOTTERY: '结束报名并转入摇号，之后不可再报名；摇号对象为当前轮候池',
  CANCELLED: '取消后批次作废，已入池房源释放'
}

/** 轮候池人数（按保障类型统计，用于摇号前提示） */
async function waitingCountOf(securityType) {
  try {
    const d = await req.get('/allocation/waiting', { params: { pageNum: 1, pageSize: 1, securityType } })
    return Number((d && d.total) || 0)
  } catch (e) { return 0 }
}

/** 批次房源套数 */
async function batchHouseCount(batchId) {
  try {
    const d = await req.get(`/allocation/batches/${batchId}/houses`, { params: { pageNum: 1, pageSize: 1 } })
    return Number((d && d.total) || 0)
  } catch (e) { return 0 }
}
async function doTransition(row, target) {
  try {
    await ElMessageBox.confirm(TRANSITION_TIP[target] || '确认变更状态？', '状态变更',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' })
  } catch (e) { return }
  try {
    await req.post(`/allocation/batches/${row.id}/status`, { batchStatus: target })
    ElMessage.success('状态已更新')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '状态变更失败')
    load()   // 刷新列表，避免前端状态与后端不一致
  }
}

watch(() => bf.orgId, (v) => {
  bf.houseIds = []
  houseOptions.value = []
  if (v) searchHouses('')
})

onMounted(() => { load(); loadOrgOptions() })
</script>
