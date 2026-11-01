<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('arrears.title') }}</h3>
      <div class="spacer" />
      <el-radio-group v-model="tab" size="small" @change="onTab">
        <el-radio-button label="action">{{ t('arrears.actionTab') }}</el-radio-button>
        <el-radio-button label="notice">{{ t('arrears.noticeTab') }}</el-radio-button>
      </el-radio-group>
    </div>

    <el-row :gutter="12" style="margin-bottom:12px">
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:2px">逾期金额趋势（近 6 月）</div>
        <LineTrend :rows="overdueTrend" color="#f56c6c" :height="170" />
      </el-col>
      <el-col :span="12">
        <div style="font-weight:600;margin-bottom:2px">逾期账单数趋势</div>
        <LineTrend :rows="countTrend" color="#e6a23c" :height="170" />
      </el-col>
    </el-row>

    <!-- ================= 欠费处置（主线：可执行动作） ================= -->
    <div v-show="tab === 'action'">
      <el-alert type="info" :closable="false" show-icon
                title="处置动作联动通行授权：冻结/解冻按此执行；默认只停门锁、不停大门（EXCLUDE_MAIN_DOOR）"
                style="margin-bottom:10px" />

      <div class="toolbar" style="margin-bottom:10px">
        <ContractSelect v-model="af.contractId" width="240px" testid="contract-select" />
        <PersonPicker v-model="af.personId" width="240px" testid="picker" />
        <el-select v-model="af.actionType" :placeholder="t('arrears.action')" clearable style="width:140px">
          <el-option v-for="t in ACTION_TYPES" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
        <el-select v-model="af.status" :placeholder="t('arrears.status')" clearable style="width:120px">
          <el-option :label="t('arrears.pending')" value="PENDING" />
          <el-option :label="t('arrears.executed')" value="EXECUTED" />
          <el-option :label="t('arrears.revoked')" value="REVOKED" />
        </el-select>
        <el-button type="primary" @click="loadActions">{{ t('arrears.search') }}</el-button>
        <el-button @click="resetActionQuery">{{ t('arrears.reset') }}</el-button>
        <el-button type="warning" @click="openScan">{{ t('arrears.scan') }}</el-button>
        <el-button type="success" @click="openAction">{{ t('arrears.create') }}</el-button>
        <span class="muted">共 {{ actionTotal }} 条</span>
      </div>

      <el-table empty-text="暂无欠费记录" :data="actions" v-loading="actionLoading" border size="small">
        <el-table-column prop="actionNo" :label="t('arrears.actionNo')" width="170" />
        <el-table-column prop="contractId" :label="t('arrears.contract')" width="160">
          <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
        </el-table-column>
        <el-table-column prop="personId" :label="t('arrears.person')" width="150">
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column :label="t('arrears.amount')" width="110" >
          <template #default="{ row }">{{ $money(row.arrearsAmount) }}</template>
        </el-table-column>
        <el-table-column prop="overdueDays" :label="t('arrears.overdueDays')" width="100" />
        <el-table-column prop="actionType" :label="t('arrears.action')" width="120">
          <template #default="{ row }">{{ enumLabel('arrearsActionType', row.actionType) }}</template>
        </el-table-column>
        <el-table-column prop="freezeScope" :label="t('arrears.scope')" width="150">
          <template #default="{ row }">
            <span v-if="row.actionType === 'FREEZE'">
              {{ row.freezeScopeLabel || enumLabel('freezeScope', row.freezeScope) }}
            </span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="actionStatus" :label="t('arrears.statusCol')" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.actionStatus)">
              {{ enumLabel('arrearsActionStatus', row.actionStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="executeTime" :label="t('arrears.executeTime')" width="170" />
        <el-table-column :label="t('arrears.actions')" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.actionStatus !== 'PENDING'"
                       @click="doExecute(row)">{{ t('arrears.execute') }}</el-button>
            <el-button link type="danger" :disabled="row.actionStatus === 'REVOKED'"
                       @click="doRevoke(row)">{{ t('arrears.revoke') }}</el-button>
            <el-button link @click="openArrearsDetail(row)">{{ t('arrears.detail') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                     :total="+actionTotal || 0" :page-size="ap.pageSize"
                     :current-page="ap.pageNum"
                     @current-change="(p) => { ap.pageNum = p; loadActions() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { ap.pageSize = s; ap.pageNum = 1; loadActions() }" />
    </div>

    <!-- ================= 催缴通知（历史记录，只读 + 登记） ================= -->
    <div v-show="tab === 'notice'">
      <el-alert type="info" :closable="false" show-icon
                :title="t('arrears.history')"
                style="margin-bottom:10px" />
      <div class="toolbar" style="margin-bottom:10px">
        <el-input v-model="keyword" :placeholder="t('arrears.keyword')" clearable style="width:160px"
                  @keyup.enter="reload" />
        <el-button type="primary" @click="reload">{{ t('arrears.search') }}</el-button>
        <el-button @click="resetQuery">{{ t('arrears.reset') }}</el-button>
        <el-input v-model.number="overdueDays" :placeholder="t('arrears.overdueMin')" style="width:120px"
                  data-testid="arrears-days" />
        <el-button @click="scan">{{ t('arrears.scanOverdue') }}</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column type="expand">
          <template #default="{ row }"><DetailView :row="row" /></template>
        </el-table-column>
        <el-table-column prop="billId" :label="t('arrears.billId')" width="150">
          <template #default="{ row }">{{ row.billIdName || row.billId }}</template>
        </el-table-column>
        <el-table-column prop="personId" :label="t('arrears.person')" width="120">
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="actionType" :label="t('arrears.method')" width="120">
          <template #default="{ row }">{{ row.actionTypeLabel || enumLabel('actionType', row.actionType) }}</template>
        </el-table-column>
        <el-table-column prop="triggerType" :label="t('arrears.level')" width="120">
          <template #default="{ row }">{{ row.dunningLevelLabel || enumLabel('dunningLevel', row.dunningLevel) }}</template>
        </el-table-column>
        <el-table-column prop="executeTime" :label="t('arrears.time')" width="170" />
        <el-table-column prop="remark" :label="t('arrears.remark')" min-width="160" />
        <el-table-column :label="t('arrears.actions')" width="90" fixed="right">
          <template #default="{ row }">
            <el-button link @click="detail = row; show = true">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                     @current-change="(p) => { pageNum = p; load() }" />
    </div>

    <!-- 扫描建议 -->
    <el-dialog v-model="scanVisible" :title="t('arrears.scanTitle')" width="740px">
      <el-alert type="warning" :closable="false" show-icon
                title="按逾期天数聚合欠费合同；「建议冻结」= 逾期较久或欠费较多，需确认安全风险后再执行" />
      <el-table :data="suggestions" border size="small" style="margin-top:10px"
                max-height="360">
        <el-table-column prop="contractId" :label="t('arrears.contract')" width="160">
          <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
        </el-table-column>
        <el-table-column prop="personId" :label="t('arrears.person')" width="150">
          <template #default="{ row }">{{ row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column label="欠费" width="110" >
          <template #default="{ row }">{{ $money(row.arrearsAmount) }}</template>
        </el-table-column>
        <el-table-column prop="overdueDays" :label="t('arrears.overdueDays')" width="100" />
        <el-table-column prop="billCount" :label="t('arrears.billCount')" width="90" />
        <el-table-column prop="freezeRecommended" :label="t('arrears.recommend')" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.freezeRecommended" type="danger" size="small">建议</el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="createFromSuggestion(row)">{{ t('arrears.generate') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="scanVisible = false">{{ t('arrears.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 新建处置 -->
    <el-dialog v-model="actionVisible" :title="t('arrears.newTitle')" width="560px">
      <el-form :model="nf" label-width="120px">
        <el-form-item :label="t('arrears.org')">
          <el-select v-model="nf.orgId" filterable clearable style="width:100%"
                     placeholder="按名称搜索组织">
            <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('arrears.contractRequired')" required>
          <ContractSelect v-model="nf.contractId" width="100%"
                          @update:model-value="() => fillFromArrears('contract')" />
        </el-form-item>
        <el-form-item :label="t('arrears.personRequired')" required>
          <PersonPicker v-model="nf.personId" width="100%"
                        @update:model-value="() => fillFromArrears('person')" />
        </el-form-item>
        <el-form-item :label="t('arrears.amountRequired')" required>
          <el-input v-model.number="nf.arrearsAmount" />
        </el-form-item>
        <el-form-item label="逾期天数">
          <el-input v-model.number="nf.overdueDays" />
        </el-form-item>
        <el-form-item label="动作类型" required>
          <el-select v-model="nf.actionType" style="width:100%">
            <el-option v-for="t in ACTION_TYPES" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="nf.actionType === 'FREEZE'" label="冻结范围">
          <el-select v-model="nf.freezeScope" style="width:100%">
            <el-option label="仅门锁（不停大门，推荐）" value="EXCLUDE_MAIN_DOOR" />
            <el-option label="仅房间门锁" value="ROOM_LOCK" />
            <el-option label="全部（含大门，需确认风险）" value="ALL" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="nf.actionType === 'FREEZE'" label="确认安全风险">
          <el-switch v-model="nf.confirmSafetyRisk" />
          <span class="muted" style="margin-left:8px">停用大门需勾选</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateAction">保存</el-button>
      </template>
    </el-dialog>

    

    <el-drawer v-model="show" title="欠费处置详情" size="720px">
      <div v-if="arrearBills.length" style="margin-bottom:12px">
        <div style="font-weight:600;margin-bottom:6px">欠费账单（未缴）</div>
        <el-table :data="arrearBills" size="small" border max-height="240">
          <el-table-column prop="billNo" label="账单号" width="165" />
          <el-table-column prop="billPeriod" label="账期" width="85" />
          <el-table-column label="费用区间" width="185">
            <template #default="{ row }">{{ row.periodStart }} ~ {{ row.periodEnd }}</template>
          </el-table-column>
          <el-table-column label="待缴" width="85" >
          <template #default="{ row }">{{ $money(row.payableAmount) }}</template>
        </el-table-column>
          <el-table-column prop="dueDate" label="截止日" width="100" />
          <el-table-column label="" width="90">
            <template #default="{ row }">
              <el-button link type="primary" @click="showExplain(row)">计费明细</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <DetailView :row="detail || {}" />
    </el-drawer>

    <el-dialog v-model="explainVisible" title="计费明细" width="640px" append-to-body>
      <div style="font-weight:600;margin-bottom:8px">{{ explainBillNo }}</div>
      <el-table :data="explainRows" size="small" border>
        <el-table-column prop="label" label="项目" width="130" />
        <el-table-column prop="value" label="值" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/**
 * 催缴管理：
 *  - 欠费处置（主线）：/fin/arrears 动作可执行（通知/冻结/限制/司法），执行与撤销留痕
 *  - 催缴通知（历史）：/fin/dunnings 已发出的通知记录，只读 + 登记
 */
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, computed, onMounted } from 'vue'
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/modules'
import req from '@/api/request'
import ContractSelect from '@/components/ContractSelect.vue'
import LineTrend from '@/components/LineTrend.vue'

const { t } = useI18n()
const tab = ref('action')

// ---------------- 欠费处置 ----------------
const ACTION_TYPES = [
  { value: 'NOTIFY', label: '通知催缴' },
  { value: 'FREEZE', label: '冻结权限' },
  { value: 'UNFREEZE', label: '解冻' },
  { value: 'RESTRICT', label: '限制续租' },
  { value: 'EXPIRE', label: '到期不续' },
  { value: 'LEGAL', label: '司法程序' }
]

const actions = ref([])
const actionTotal = ref(0)
const actionLoading = ref(false)
const ap = reactive({ pageNum: 1, pageSize: 20 })
const af = reactive({ contractId: undefined, personId: undefined,
  actionType: undefined, status: undefined })

async function loadActions() {
  actionLoading.value = true
  try {
    const params = { pageNum: ap.pageNum, pageSize: ap.pageSize }
    if (af.contractId) params.contractId = af.contractId
    if (af.personId) params.personId = af.personId
    if (af.actionType) params.actionType = af.actionType
    if (af.status) params.status = af.status
    const d = await req.get('/fin/arrears', { params })
    actions.value = d.rows || []
    actionTotal.value = Number(d.total || 0)
  } catch (e) {
    actions.value = []; actionTotal.value = 0
  } finally {
    actionLoading.value = false
  }
}

function resetActionQuery() {
  af.contractId = undefined; af.personId = undefined
  af.actionType = undefined; af.status = undefined
  ap.pageNum = 1
  loadActions()
}

function statusType(s) {
  if (s === 'EXECUTED') return 'success'
  if (s === 'REVOKED') return 'info'
  if (s === 'FAILED') return 'danger'
  return 'warning'
}

async function doExecute(row) {
  try {
    await ElMessageBox.confirm(
      `确认执行「${enumLabel('arrearsActionType', row.actionType)}」？`
      + (row.actionType === 'FREEZE' ? '将联动冻结门锁授权。' : ''),
      '执行处置', { type: 'warning' })
    await req.post(`/fin/arrears/${row.id}/execute`)
    ElMessage.success('已执行')
    loadActions()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.message || '执行失败')
  }
}

async function doRevoke(row) {
  try {
    const { value } = await ElMessageBox.prompt('撤销原因（如已缴清）', '撤销处置',
      { inputPlaceholder: '必填', inputValidator: (v) => (v && v.trim() ? true : '请填写原因') })
    await req.post(`/fin/arrears/${row.id}/revoke`, { reason: value })
    ElMessage.success('已撤销')
    loadActions()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e?.response?.data?.message || '撤销失败')
  }
}

const scanVisible = ref(false)
const suggestions = ref([])

async function openScan() {
  try {
    const d = await req.get('/fin/arrears/scan',
      { params: { minOverdueDays: overdueDays.value || 3 } })
    suggestions.value = d || []
    scanVisible.value = true
    if (!suggestions.value.length) ElMessage.info('没有达到阈值的欠费合同')
  } catch (e) {
    ElMessage.error('扫描失败')
  }
}

const actionVisible = ref(false)
const nf = reactive({ orgId: '', contractId: undefined, personId: undefined,
  arrearsAmount: undefined, overdueDays: undefined, actionType: 'NOTIFY',
  freezeScope: 'EXCLUDE_MAIN_DOOR', confirmSafetyRisk: false })

const orgOptions = ref([])
async function loadOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = (d && d.rows) || []
  } catch (e) { orgOptions.value = [] }
}

/** 输入合同或人员后，自动带出欠费金额、逾期天数与另一方 */
async function fillFromArrears(source) {
  const params = {}
  if (source === 'contract') {
    params.contractId = nf.contractId || undefined
  } else {
    params.personId = nf.personId || undefined
  }
  if (!params.contractId && !params.personId) return
  try {
    const d = await req.get('/fin/arrears/summary', { params })
    if (!d) return
    if (source === 'contract') {
      if (d.person_id) nf.personId = d.person_id
    } else if (d.contract_id) {
      nf.contractId = d.contract_id
    }
    if (d.org_id) nf.orgId = String(d.org_id)
    if (d.amount != null) nf.arrearsAmount = Number(d.amount)
    if (d.days != null) nf.overdueDays = Number(d.days)
  } catch (e) { /* 保留手填 */ }
}

function openAction() {
  loadOrgs()
  Object.assign(nf, { orgId: '', contractId: undefined, personId: undefined,
    arrearsAmount: undefined, overdueDays: undefined, actionType: 'NOTIFY',
    freezeScope: 'EXCLUDE_MAIN_DOOR', confirmSafetyRisk: false })
  actionVisible.value = true
}

function createFromSuggestion(s) {
  Object.assign(nf, {
    contractId: s.contractId, personId: s.personId,
    arrearsAmount: Number(s.arrearsAmount), overdueDays: s.overdueDays,
    actionType: s.freezeRecommended ? 'FREEZE' : 'NOTIFY',
    freezeScope: 'EXCLUDE_MAIN_DOOR', confirmSafetyRisk: false
  })
  scanVisible.value = false
  actionVisible.value = true
}

async function doCreateAction() {
  if (!nf.contractId || !nf.personId || !nf.arrearsAmount) {
    ElMessage.warning('请填写合同、人员与欠费金额')
    return
  }
  saving.value = true
  try {
    await req.post('/fin/arrears', { ...nf, triggerType: 'MANUAL' })
    ElMessage.success('处置已创建')
    actionVisible.value = false
    loadActions()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally {
    saving.value = false
  }
}

// ---------------- 催缴通知 ----------------
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const overdueDays = ref(3)
const show = ref(false)
const detail = ref(null)
const arrearBills = ref([])
const explainVisible = ref(false)
const explainRows = ref([])
const explainBillNo = ref('')

async function showExplain(bill) {
  explainBillNo.value = bill.billNo
  explainRows.value = []
  explainVisible.value = true
  try {
    const e = await req.get('/fin/bills/' + bill.id + '/explain')
    explainRows.value = (e && e.lines) || []
  } catch (err) { explainRows.value = [] }
}

async function openArrearsDetail(row) {
  detail.value = row
  show.value = true
  arrearBills.value = []
  if (!row.contractId) return
  try {
    const d = await req.get('/fin/bills', { params: { pageNum: 1, pageSize: 30,
      contractId: row.contractId, status: 'UNPAID' } })
    arrearBills.value = (d && d.rows) || []
  } catch (e) { arrearBills.value = [] }
}

const trendRows = ref([])
const overdueTrend = computed(() => trendRows.value.map((m) => ({
  label: String(m.month || '').slice(5), value: Number(m.overdueAmount) || 0
})))
const countTrend = computed(() => trendRows.value.map((m) => ({
  label: String(m.month || '').slice(5), value: Number(m.overdueBills) || 0
})))

async function loadTrend() {
  try {
    trendRows.value = await req.get('/fin/arrears/trend', { params: { months: 6 } }) || []
  } catch (e) { trendRows.value = [] }
}

async function load() {
  loading.value = true
  try {
    const d = await financeApi.arrears({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}

function reload() { pageNum.value = 1; load() }


async function scan() {
  const r = await financeApi.dunningScan({
    minOverdueDays: overdueDays.value || undefined
  })
  ElMessage.success(`扫描完成（逾期≥${overdueDays.value} 天）：生成 ` +
    (r?.count ?? (Array.isArray(r) ? r.length : '若干')) + ' 条催缴通知')
  load()
}

function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}

function onTab() {
  if (tab.value === 'action') loadActions()
  else load()
}

onMounted(() => { loadTrend(); loadActions(); load() })
</script>
