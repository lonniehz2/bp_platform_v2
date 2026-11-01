<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('review.title') }}</h3>
      <el-tag size="small" type="info">{{ t('review.tagline') }}</el-tag>
      <div class="spacer" />
      <el-button type="success" @click="batchVisible = true">{{ t('review.batch') }}</el-button>
      <el-button @click="load">{{ t('review.refresh') }}</el-button>
    </div>
    <el-alert type="info" :closable="false" show-icon
              :title="t('misc3.annualTip')"
              style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('misc.emptyDefault')">
      <el-table-column prop="reviewNo" :label="t('review.no')" width="170" />
      <el-table-column prop="contractId" :label="t('review.contract')" width="130">
        <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
      </el-table-column>
      <el-table-column prop="personId" :label="t('review.person')" width="110">
        <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
      </el-table-column>
      <el-table-column prop="reviewYear" :label="t('review.year')" width="90" />
      <el-table-column prop="reviewResult" :label="t('review.result')" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.reviewResult === 'EXIT' ? 'danger'
            : (row.reviewResult === 'ADJUST' ? 'warning' : 'success')">
            {{ row.reviewResultLabel || enumLabel('reviewResult', row.reviewResult) || '待复核' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="reviewStatus" :label="t('review.status')" width="110">
        <template #default="{ row }">{{ row.reviewStatusLabel || enumLabel('reviewStatus', row.reviewStatus) }}</template>
      </el-table-column>
      <el-table-column :label="t('review.actions')" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('review.detail') }}</el-button>
          <el-button link type="primary" @click="openReview(row)">{{ t('review.review') }}</el-button>
          <el-button link type="warning" @click="openRent(row)">{{ t('review.rentAdjust') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="q.pageSize" :current-page="q.pageNum"
                   @current-change="(p) => { q.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { q.pageSize = s; q.pageNum = 1; load() }" />

    <el-dialog v-model="batchVisible" :title="t('review.batchTitle')" width="480px">
      <el-form :model="b" label-width="110px">
        <el-form-item :label="t('review.reviewYear')"><el-input v-model="b.reviewYear"
          placeholder="2026" /></el-form-item>
        <el-form-item :label="t('review.org')"><OrgSelect v-model="b.orgId" width="100%" /></el-form-item>
        <el-form-item :label="t('review.batchNo')"><el-input v-model="b.reviewBatch" /></el-form-item>
        <el-form-item :label="t('review.dryRun')">
          <el-switch v-model="b.dryRun" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchVisible = false">{{ t('review.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doBatch">{{ t('review.start') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reviewVisible" :title="t('review.reviewTitle')" width="500px">
      <el-form :model="r" label-width="110px">
        <el-form-item :label="t('review.conclusion')">
          <el-select v-model="r.reviewResult" style="width:100%">
            <el-option :label="t('review.keep')" value="KEEP" />
            <el-option :label="t('review.adjust')" value="ADJUST" />
            <el-option :label="t('review.exit')" value="EXIT" />
          </el-select></el-form-item>
        <el-form-item :label="t('review.newRent')">
          <el-input v-model.number="r.newMonthlyRent" /></el-form-item>
        <el-form-item :label="t('review.opinion')">
          <el-input v-model="r.opinion" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">{{ t('review.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doReview">{{ t('review.submit') }}</el-button>
      </template>
    </el-dialog>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('review.detail')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView） */
const { t } = useI18n()
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
  orgId: null, reviewBatch: '', dryRun: false })
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
