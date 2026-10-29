<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">年审复核</h3>
      <el-tag size="small" type="info">保留 / 调租 / 退出</el-tag>
      <div class="spacer" />
      <el-button type="success" @click="batchVisible = true">批量发起年审</el-button>
      <el-button @click="load">刷新</el-button>
    </div>
    <el-alert type="info" :closable="false" show-icon
              title="年审判定为「退出」会自动生成腾退单（类型用 OTHER，避免误触发 5 年禁申）"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="reviewNo" label="年审单号" width="170" />
      <el-table-column prop="contractId" label="合同" width="130">
        <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
      </el-table-column>
      <el-table-column prop="personId" label="人员" width="110">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="reviewYear" label="年度" width="90" />
      <el-table-column prop="reviewResult" label="结论" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.reviewResult === 'EXIT' ? 'danger'
            : (row.reviewResult === 'ADJUST' ? 'warning' : 'success')">
            {{ row.reviewResultLabel || enumLabel('reviewResult', row.reviewResult) || '待复核' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reviewStatus" label="状态" width="110">
        <template #default="{ row }">{{ row.reviewStatusLabel || enumLabel('reviewStatus', row.reviewStatus) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="primary" @click="openReview(row)">复核</el-button>
          <el-button link type="warning" @click="openRent(row)">调租</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="q.pageSize" :current-page="q.pageNum"
                   @current-change="(p) => { q.pageNum = p; load() }" />

    <el-dialog v-model="batchVisible" title="批量发起年审" width="480px">
      <el-form :model="b" label-width="110px">
        <el-form-item label="复核年度"><el-input v-model="b.reviewYear"
          placeholder="2026" /></el-form-item>
        <el-form-item label="组织"><OrgSelect v-model="b.orgId" width="100%" /></el-form-item>
        <el-form-item label="批次号"><el-input v-model="b.reviewBatch" /></el-form-item>
        <el-form-item label="试算（不落库）">
          <el-switch v-model="b.dryRun" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doBatch">发起</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewVisible" title="年审复核" width="500px">
      <el-form :model="r" label-width="110px">
        <el-form-item label="复核结论">
          <el-select v-model="r.reviewResult" style="width:100%">
            <el-option label="保留资格" value="KEEP" />
            <el-option label="调整租金/补贴" value="ADJUST" />
            <el-option label="退出保障" value="EXIT" />
          </el-select></el-form-item>
        <el-form-item label="新租金（调租时）">
          <el-input v-model.number="r.newMonthlyRent" /></el-form-item>
        <el-form-item label="复核意见">
          <el-input v-model="r.opinion" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doReview">提交</el-button>
      </template>
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
import { annualReviewApi } from '@/api/modules'
import req from '@/api/request'
import OrgSelect from '@/components/OrgSelect.vue'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const q = reactive({ pageNum: 1, pageSize: 20 })
const batchVisible = ref(false)
const reviewVisible = ref(false)
const current = ref(null)
const b = reactive({ reviewYear: String(new Date().getFullYear()),
  orgId: 1, reviewBatch: '', dryRun: false })
const r = reactive({ reviewResult: 'KEEP', newMonthlyRent: null, opinion: '' })

async function load() {
  loading.value = true
  try {
    const d = await annualReviewApi.page({ ...q })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}

async function doBatch() {
  await ElMessageBox.confirm('将为符合条件的人员批量发起年审，是否继续？',
    '确认批量年审', { type: 'warning' })
  saving.value = true
  try {
    const res = await annualReviewApi.batch({ ...b })
    ElMessage.success('已发起年审：' + (res?.count ?? res ?? '完成'))
    batchVisible.value = false; load()
  } finally { saving.value = false }
}

function openReview(row) {
  current.value = row
  r.reviewResult = 'KEEP'; r.newMonthlyRent = null; r.opinion = ''
  reviewVisible.value = true
}
async function doReview() {
  saving.value = true
  try {
    await annualReviewApi.start(current.value.id)
    await annualReviewApi.finish(current.value.id, { ...r })
    ElMessage.success('复核完成')
    reviewVisible.value = false; load()
  } finally { saving.value = false }
}

onMounted(load)
/** 复核后调整租金：生成合同变更单 */
const rentVisible = ref(false)
const rentRow = ref({})
const rentForm = reactive({ newMonthlyRent: null, reason: '年审收入变化调租' })

function openRent(row) {
  rentRow.value = row
  rentForm.newMonthlyRent = row.currentRent || row.monthlyRent || null
  rentVisible.value = true
}

async function doRentChange() {
  if (!rentForm.newMonthlyRent) {
    ElMessage.warning('请填写新租金'); return
  }
  await req.post(`/annual-reviews/${rentRow.value.id}/rent-change`, {
    newMonthlyRent: rentForm.newMonthlyRent, reason: rentForm.reason
  })
  ElMessage.success('已生成调租变更单')
  rentVisible.value = false
  load()
}
</script>
