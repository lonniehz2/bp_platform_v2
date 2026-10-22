<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">配租批次</h3>
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
        <template #more>
          <el-input v-model="af.orgId" placeholder="组织 ID" clearable style="width:200px" />
        </template>
      </FilterBar>

      <el-table :data="batches" v-loading="loading" border size="small">
        <el-table-column prop="id" label="批次ID" width="140" />
        <el-table-column prop="batchNo" label="批次号" width="160" />
        <el-table-column prop="batchName" label="名称" />
        <el-table-column prop="batchStatus" label="状态" width="110">
          <template #default="{ row }">{{ row.batchStatusLabel || enumLabel('batchStatus', row.batchStatus) }}</template>
        </el-table-column>
        <el-table-column prop="houseCount" label="房源数" width="90" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
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
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
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
        <el-table-column prop="queueId" label="轮候ID" width="140">
          <template #default="{ row }">{{ row.queueIdName || row.queueId }}</template>
        </el-table-column>
        <el-table-column prop="personId" label="人员" width="120">
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="totalScore" label="总分" width="100" />
        <el-table-column prop="rankNo" label="名次" width="90" />
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
import { ref, reactive, onMounted } from 'vue'
import DetailView from '@/components/DetailView.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { allocationApi } from '@/api/modules'
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
  await ElMessageBox.confirm(
    `确认对批次「${row.batchName || row.batchNo}」执行摇号？种子：${seed.value}`,
    '摇号确认', { type: 'warning' })
  const res = await allocationApi.lottery(row.id, seed.value)
  ElMessage.success(`摇号完成：中签 ${res?.winCount ?? res?.length ?? 0} 人`)
  viewResults(row)
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

onMounted(load)
</script>
