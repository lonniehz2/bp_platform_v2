<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="query.applicationStatus" placeholder="状态" clearable
                   style="width:150px" @change="load">
          <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
        </el-select>
        <PersonPicker v-model="query.personId" width="260px" testid="app-person-picker" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button @click="resetQuery">清空</el-button>
        <div class="spacer" />
        <el-button type="success" @click="openCreate">
          <el-icon><Plus /></el-icon>新建申请
        </el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="applicationNo" label="申请编号" width="160" />
        <el-table-column prop="personName" label="申请人" width="110">
        <template #default="{ row }">
          {{ row.personName || row.personId }}
        </template>
      </el-table-column>
        <el-table-column prop="securityType" label="保障类型" width="120">
          <template #default="{ row }">{{ row.securityTypeLabel || enumLabel('securityType', row.securityType) }}</template>
        </el-table-column>
        <el-table-column prop="familySize" label="家庭人口" width="90" />
        <el-table-column prop="incomePerCapita" label="人均收入" width="110" />
        <el-table-column prop="applicationStatusLabel" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="tagOf(row.applicationStatus)" size="small">
              {{ row.applicationStatusLabel || row.applicationStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="currentNode" label="当前环节" width="100">
        <template #default="{ row }">{{ row.currentNodeLabel || enumLabel('currentNode', row.currentNode) }}</template>
      </el-table-column>
        <el-table-column prop="applyTime" label="申请时间" width="170" />
        <el-table-column label="操作" width="290" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
            <el-button v-if="row.applicationStatus === 'SUBMITTED'" link type="success"
                       @click="accept(row)" data-testid="row-accept">受理</el-button>
            <el-button v-if="row.applyChannel === 'OFFLINE'
                       && ['SUBMITTED','ACCEPTED','REVIEWING'].includes(row.applicationStatus)"
                       link type="warning" data-testid="row-offline-pass"
                       @click="offlinePass(row)">线下通过</el-button>
            <el-button v-if="canReview(row)" link type="primary"
                       @click="openReview(row)">审核</el-button>
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
          <el-input v-model="form.orgId" />
        </el-form-item>
        <el-form-item label="申请人ID">
          <PersonPicker v-model="form.personId" width="240px" testid="person-picker" />
        </el-form-item>
        <el-form-item label="保障类型">
          <el-select v-model="form.securityType">
            <el-option v-for="o in securityTypeOptions" :key="o.value"
                       :label="o.label" :value="o.value" />
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
        <el-descriptions-item label="保障类型">{{ enumLabel('securityType', current?.securityType) }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ current?.applicationStatusLabel }}</el-descriptions-item>
      </el-descriptions>
      <el-alert type="info" :closable="false" show-icon
                title="「通过」前系统会按保障档案校验：收入档位、家庭人口一致性、人才认定有效期、名下房产" />
      <el-form :model="reviewForm" label-width="90px" style="margin-top:12px">
        <el-form-item label="审核阶段">
          <el-select v-model="reviewForm.stage" disabled>
            <el-option label="受理初审" value="ACCEPT" />
            <el-option label="形式审查" value="FORM" />
            <el-option label="多部门联审" value="JOINT" />
            <el-option label="终审" value="FINAL" />
          </el-select>
          <div class="muted" style="font-size:12px;margin-left:8px">
            必须按 受理初审 → 形式审查 → 联审 → 终审 逐级通过
          </div>
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
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { applicationApi } from '@/api/modules'
import { useDict } from '@/composables/useDict'

const statuses = ['DRAFT', 'SUBMITTED', 'ACCEPTED', 'REVIEWING', 'SUPPLEMENT',
  'APPROVED', 'REJECTED', 'CANCELLED']

// 保障类型走系统字典（可后台维护，无需改前端）
const { options: securityTypeOptions } = useDict('SECURITY_TYPE', [
  { value: 'PUBLIC', label: '公租房' },
  { value: 'AFFORDABLE', label: '保障性租赁住房' },
  { value: 'TALENT', label: '人才公寓' },
  { value: 'LOW_RENT', label: '廉租住房' }
])

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
      // 后端参数名是 status（不是 applicationStatus），传错会被静默忽略
      status: query.applicationStatus || undefined,
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


/** 只有已受理/审核中/补件状态可以审核 */
function canReview(row) {
  return ['ACCEPTED', 'REVIEWING', 'SUPPLEMENT'].includes(row.applicationStatus)
}

/** 受理：已提交 → 已受理 */
async function accept(row) {
  try {
    await req.post(`/applications/${row.id}/accept`, {})
    ElMessage.success('已受理')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '受理失败')
  }
}

function openReview(row) {
  current.value = row
  reviewForm.stage = stageOfNode(row.currentNode)
  reviewForm.result = 'PASS'
  reviewForm.opinion = ''
  reviewVisible.value = true
}

/** 当前环节 → 审核阶段（默认值，锁定不可跳级） */
function stageOfNode(node) {
  return ['ACCEPT', 'FORM', 'JOINT', 'FINAL'].includes(node) ? node : 'FINAL'
}

/** 线下受理通过：先受理（如未受理），再做终审通过 */
async function offlinePass(row) {
  await ElMessageBox.confirm(
    '线下渠道申请将直接受理并终审通过（仍会校验保障档案资格）。确认？',
    '线下通过', { type: 'warning' })
  saving.value = true
  try {
    if (row.applicationStatus === 'SUBMITTED') {
      await req.post(`/applications/${row.id}/accept`, {})
    }
    await applicationApi.review(row.id, {
      stage: 'FINAL',
      result: 'PASS',
      opinion: row.offlineRemark || '线下渠道受理，材料齐备，审核通过'
    })
    ElMessage.success('已线下通过')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '线下通过失败')
  } finally { saving.value = false }
}

async function doReview() {
  saving.value = true
  try {
    await applicationApi.review(current.value.id, { ...reviewForm })
    ElMessage.success('审核已提交')
    reviewVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '审核提交失败')
  } finally {
    saving.value = false
  }
}

async function openRecords(row) {
  // 后端真实路径是 /reviews（审核记录）\n  records.value = await applicationApi.reviews(row.id)
  recordsVisible.value = true
}

const query0 = JSON.parse(JSON.stringify(query))
function resetQuery() {
  Object.assign(query, query0)
  load()
}

// 从待办中心「待审申请」点进来时带 pending=1，这里把状态筛选设为待审
if (/pending=1/.test(window.location.hash)) {
  query.applicationStatus = 'SUBMITTED'
}
onMounted(load)
</script>
