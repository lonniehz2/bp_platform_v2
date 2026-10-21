# -*- coding: utf-8 -*-
"""生成前端页面：Dashboard / Applications / Allocations"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

F['src/views/Dashboard.vue'] = '''<template>
  <div>
    <div class="toolbar">
      <h3 style="margin:0">运营驾驶舱</h3>
      <el-tag type="info" size="small">{{ screen?.screenName || '总览' }}</el-tag>
      <span class="muted">刷新间隔 {{ screen?.refreshSeconds || '-' }}s</span>
      <div class="spacer" />
      <el-button :loading="loading" @click="load">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <div class="stat-grid">
      <div v-for="w in widgets" :key="w.code"
           :class="['stat-card', toneOf(w)]">
        <div class="label">{{ w.title }}</div>
        <div class="value">{{ fmt(w.value) }}</div>
        <div class="muted">{{ w.chart }}</div>
      </div>
    </div>

    <div class="page-card" style="margin-top:16px">
      <h4 style="margin:0 0 12px">指标明细</h4>
      <el-table :data="metricRows" size="small" border>
        <el-table-column prop="code" label="指标编码" width="240" />
        <el-table-column prop="value" label="当前值" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { rptApi } from '@/api/modules'

const loading = ref(false)
const screen = ref(null)
const widgets = ref([])
const metrics = ref({})

// 单位与阈值提示
const UNITS = {
  OCCUPANCY_RATE: '%', BILL_UNPAID_AMOUNT: '元', PAYMENT_TOTAL_AMOUNT: '元'
}

function fmt(v) {
  if (v === null || v === undefined) return '-'
  const n = Number(v)
  return Number.isFinite(n) ? n.toLocaleString('zh-CN') : v
}

function toneOf(w) {
  if (w.code === 'ACCESS_ABNORMAL_COUNT' && Number(w.value) > 0) return 'danger'
  if (w.code === 'BILL_UNPAID_COUNT' && Number(w.value) > 0) return 'warn'
  if (w.code === 'OCCUPANCY_RATE') return 'ok'
  return ''
}

const metricRows = computed(() =>
  Object.entries(metrics.value)
    .filter(([k]) => k !== 'generatedAt')
    .map(([code, value]) => ({ code, value: fmt(value) }))
)

async function load() {
  loading.value = true
  try {
    const data = await rptApi.screenData('OVERVIEW')
    screen.value = data
    widgets.value = (data.widgets || []).map((w) => ({
      ...w,
      title: w.title + (UNITS[w.code] ? `（${UNITS[w.code]}）` : '')
    }))
    metrics.value = await rptApi.metrics()
  } catch (e) {
    // 拦截器已提示
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
'''

F['src/views/Applications.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="query.applicationStatus" placeholder="状态" clearable
                   style="width:150px" @change="load">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
        <el-input v-model="query.personId" placeholder="申请人ID" clearable
                  style="width:160px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <div class="spacer" />
        <el-button type="success" @click="openCreate">
          <el-icon><Plus /></el-icon>新建申请
        </el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="applicationNo" label="申请编号" width="160" />
        <el-table-column prop="personId" label="申请人" width="110" />
        <el-table-column prop="securityType" label="保障类型" width="120" />
        <el-table-column prop="familySize" label="家庭人口" width="90" />
        <el-table-column prop="incomePerCapita" label="人均收入" width="110" />
        <el-table-column prop="applicationStatusLabel" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="tagOf(row.applicationStatus)" size="small">
              {{ row.applicationStatusLabel || row.applicationStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="currentNode" label="当前环节" width="100" />
        <el-table-column prop="applyTime" label="申请时间" width="170" />
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openReview(row)">审核</el-button>
            <el-button link @click="openRecords(row)">轨迹</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }" />
    </div>

    <!-- 新建申请 -->
    <el-dialog v-model="createVisible" title="新建申请" width="560px">
      <el-form :model="form" label-width="110px">
        <el-form-item label="受理组织ID">
          <el-input v-model.number="form.orgId" />
        </el-form-item>
        <el-form-item label="申请人ID">
          <el-input v-model.number="form.personId" />
        </el-form-item>
        <el-form-item label="保障类型">
          <el-select v-model="form.securityType">
            <el-option label="公租房" value="PUBLIC" />
            <el-option label="保障性租赁住房" value="AFFORDABLE" />
            <el-option label="人才公寓" value="TALENT" />
            <el-option label="廉租住房" value="LOW_RENT" />
          </el-select>
        </el-form-item>
        <el-form-item label="保障方式">
          <el-select v-model="form.securityMode">
            <el-option label="实物配租" value="HOUSE" />
            <el-option label="租赁补贴" value="SUBSIDY" />
          </el-select>
        </el-form-item>
        <el-form-item label="申请渠道">
          <el-select v-model="form.applyChannel">
            <el-option label="线上" value="ONLINE" />
            <el-option label="线下" value="OFFLINE" />
          </el-select>
        </el-form-item>
        <el-form-item label="家庭人口">
          <el-input v-model.number="form.familySize" />
        </el-form-item>
        <el-form-item label="家庭月收入">
          <el-input v-model.number="form.declaredIncome" />
        </el-form-item>
        <el-alert type="warning" :closable="false" show-icon
                  title="提交前会自动校验：信用惩戒、实名认证、承诺书签署" />
        <el-form-item label="签署承诺书" style="margin-top:8px">
          <el-switch v-model="form.complianceCommitFlag" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="同意核实">
          <el-switch v-model="form.dataShareAgreeFlag" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">提交</el-button>
      </template>
    </el-dialog>

    <!-- 审核 -->
    <el-dialog v-model="reviewVisible" title="资格审核" width="560px">
      <el-descriptions :column="2" border size="small" style="margin-bottom:14px">
        <el-descriptions-item label="申请编号">{{ current?.applicationNo }}</el-descriptions-item>
        <el-descriptions-item label="申请人">{{ current?.personId }}</el-descriptions-item>
        <el-descriptions-item label="保障类型">{{ current?.securityType }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ current?.applicationStatusLabel }}</el-descriptions-item>
      </el-descriptions>
      <el-alert type="info" :closable="false" show-icon
                title="「通过」前系统会按保障档案校验：收入档位、家庭人口一致性、人才认定有效期、名下房产" />
      <el-form :model="reviewForm" label-width="90px" style="margin-top:12px">
        <el-form-item label="审核阶段">
          <el-select v-model="reviewForm.stage">
            <el-option label="受理初审" value="ACCEPT" />
            <el-option label="形式审查" value="FORM" />
            <el-option label="多部门联审" value="JOINT" />
            <el-option label="终审" value="FINAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="审核结果">
          <el-radio-group v-model="reviewForm.result">
            <el-radio value="PASS">通过</el-radio>
            <el-radio value="REJECT">不通过</el-radio>
            <el-radio value="SUPPLEMENT">需补件</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="意见">
          <el-input v-model="reviewForm.opinion" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doReview">提交</el-button>
      </template>
    </el-dialog>

    <!-- 轨迹 -->
    <el-drawer v-model="recordsVisible" title="审核轨迹" size="520px">
      <el-timeline>
        <el-timeline-item v-for="r in records" :key="r.id"
                          :timestamp="r.reviewTime" placement="top">
          <b>{{ r.reviewStage }} · {{ r.reviewResult }}</b>
          <div class="muted">{{ r.reviewUserName }} — {{ r.reviewOpinion }}</div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!records.length" description="暂无审核记录" />
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { applicationApi } from '@/api/modules'

const statuses = ['DRAFT', 'SUBMITTED', 'ACCEPTED', 'REVIEWING', 'SUPPLEMENT',
  'APPROVED', 'REJECTED', 'CANCELLED']

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, applicationStatus: '', personId: '' })

const createVisible = ref(false)
const form = reactive({
  orgId: 1, personId: null, securityType: 'PUBLIC', securityMode: 'HOUSE',
  applyChannel: 'ONLINE', familySize: 1, declaredIncome: null,
  complianceCommitFlag: 1, dataShareAgreeFlag: 1
})

const reviewVisible = ref(false)
const current = ref(null)
const reviewForm = reactive({ stage: 'FINAL', result: 'PASS', opinion: '' })

const recordsVisible = ref(false)
const records = ref([])

function tagOf(s) {
  return ({ APPROVED: 'success', REJECTED: 'danger', SUPPLEMENT: 'warning',
    REVIEWING: 'primary', ACCEPTED: 'info' })[s] || 'info'
}

async function load() {
  loading.value = true
  try {
    const data = await applicationApi.page({
      pageNum: query.pageNum, pageSize: query.pageSize,
      applicationStatus: query.applicationStatus || undefined,
      personId: query.personId || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  createVisible.value = true
}

async function save() {
  saving.value = true
  try {
    await applicationApi.create({ ...form })
    ElMessage.success('申请已创建')
    createVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

function openReview(row) {
  current.value = row
  reviewForm.result = 'PASS'
  reviewForm.opinion = ''
  reviewVisible.value = true
}

async function doReview() {
  saving.value = true
  try {
    await applicationApi.review(current.value.id, { ...reviewForm })
    ElMessage.success('审核已提交')
    reviewVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function openRecords(row) {
  records.value = await applicationApi.records(row.id)
  recordsVisible.value = true
}

onMounted(load)
</script>
'''

F['src/views/Allocations.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">配租批次</h3>
        <div class="spacer" />
        <el-input v-model="seed" placeholder="摇号种子（可复现）" style="width:200px" />
        <el-button type="primary" @click="load">刷新</el-button>
      </div>

      <el-table :data="batches" v-loading="loading" border size="small">
        <el-table-column prop="id" label="批次ID" width="140" />
        <el-table-column prop="batchNo" label="批次号" width="160" />
        <el-table-column prop="batchName" label="名称" />
        <el-table-column prop="batchStatus" label="状态" width="110" />
        <el-table-column prop="houseCount" label="房源数" width="90" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
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
        <el-table-column prop="personId" label="人员" width="110" />
        <el-table-column prop="houseId" label="房源" width="110" />
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
        <el-table-column prop="queueId" label="轮候ID" width="140" />
        <el-table-column prop="personId" label="人员" width="120" />
        <el-table-column prop="totalScore" label="总分" width="100" />
        <el-table-column prop="rankNo" label="名次" width="90" />
        <el-table-column prop="resultType" label="结果" width="100" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { allocationApi } from '@/api/modules'

const loading = ref(false)
const batches = ref([])
const allocations = ref([])
const results = ref([])
const resultVisible = ref(false)
const seed = ref('20261019')

async function load() {
  loading.value = true
  try {
    const b = await allocationApi.batches({ pageNum: 1, pageSize: 50 })
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
'''

count = 0
for rel, content in F.items():
    path = os.path.join(BASE, rel.replace('/', '\\'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    io.open(path, 'w', encoding='utf-8').write(content)
    count += 1
print('生成 %d 个页面' % count)
