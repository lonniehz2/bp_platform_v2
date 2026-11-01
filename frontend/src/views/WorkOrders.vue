<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('workorder.title') }}</h3>
      <el-select v-model="query.orderStatus" :placeholder="t('workorder.status')" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
      </el-select>
      <div class="spacer" />
      <el-button type="warning" plain @click="openPlans" data-testid="inspection-plans">{{ t('workorder.plans') }}</el-button>
      <el-button plain :loading="saving" @click="autoAssignPending"
                 data-testid="wo-autoassign-all">{{ t('workorder.batchAssign') }}</el-button>
      <el-button plain :loading="saving" @click="escalateOverdue"
                 data-testid="wo-escalate">{{ t('workorder.escalate') }}</el-button>
      <el-button type="primary" @click="reload">{{ t('workorder.refresh') }}</el-button>
    </div>

    <!-- 巡检计划（物业）：按周期自动生成工单 -->
    <el-dialog v-model="plansVisible" :title="t('workorder.planTitle')" width="900px">
      <div style="display:flex;gap:8px;margin-bottom:10px">
        <el-button type="success" size="small" @click="planFormVisible = true">{{ t('workorder.newPlan') }}</el-button>
        <el-button type="warning" size="small" :loading="saving" @click="runDue">{{ t('workorder.runDue') }}</el-button>
        <div style="flex:1" />
        <span class="muted" style="font-size:12px;align-self:center">
          {{ t('workorder.dueHint') }}
        </span>
      </div>
      <el-table :data="plans" size="small" border max-height="360" :empty-text="t('workorder.empty')">
        <el-table-column prop="planName" :label="t('workorder.planName')" min-width="160" />
        <el-table-column prop="inspectType" :label="t('workorder.type')" width="110">
          <template #default="{ row }">
            {{ { SAFETY: t('workorder.inspectSafety'), EQUIPMENT: t('workorder.inspectEquipment'), CLEANING: t('workorder.inspectCleaning'), GREEN: t('workorder.inspectGreen') }[row.inspectType] || row.inspectType }}
          </template>
        </el-table-column>
        <el-table-column prop="frequency" :label="t('workorder.frequency')" width="90">
          <template #default="{ row }">
            {{ { DAY: t('workorder.freqDay'), WEEK: t('workorder.freqWeek'), MONTH: t('workorder.freqMonth') }[row.frequency] || row.frequency }}
          </template>
        </el-table-column>
        <el-table-column prop="nextRunDate" :label="t('workorder.nextRun')" width="120" />
        <el-table-column prop="assignUserName" :label="t('workorder.owner')" width="110" />
        <el-table-column prop="planStatus" :label="t('workorder.planStatus')" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.planStatus === 'ENABLED' ? 'success' : 'info'">
              {{ row.planStatus === 'ENABLED' ? t('workorder.planEnabled') : t('workorder.planDisabled') }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 新建巡检计划 -->
    <el-dialog v-model="planFormVisible" :title="t('workorder.createPlanTitle')" width="520px">
      <el-form :model="pf" label-width="100px">
        <el-form-item :label="t('workorder.planName')" required>
          <el-input v-model="pf.planName" :placeholder="t('workorder.planNameHint')" />
        </el-form-item>
        <el-form-item :label="t('workorder.type')">
          <el-select v-model="pf.inspectType" style="width:100%">
            <el-option :label="t('workorder.safety')" value="SAFETY" />
            <el-option :label="t('workorder.equipment')" value="EQUIPMENT" />
            <el-option :label="t('workorder.cleaning')" value="CLEANING" />
            <el-option :label="t('workorder.green')" value="GREEN" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('workorder.cycle')">
          <el-radio-group v-model="pf.frequency">
            <el-radio-button value="DAY">{{ t('workorder.daily') }}</el-radio-button>
            <el-radio-button value="WEEK">{{ t('workorder.weekly') }}</el-radio-button>
            <el-radio-button value="MONTH">{{ t('workorder.monthly') }}</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('workorder.firstRun')">
          <el-date-picker v-model="pf.nextRunDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('workorder.owner')">
          <el-input v-model="pf.assignUserName" :placeholder="t('workorder.ownerHint')" />
        </el-form-item>
        <el-form-item :label="t('workorder.remark')">
          <el-input v-model="pf.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planFormVisible = false">{{ t('workorder.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doCreatePlan">{{ t('workorder.create') }}</el-button>
      </template>
    </el-dialog>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="workorderNo" :label="t('workorder.no')" width="180" />
      <el-table-column prop="orderType" :label="t('workorder.orderType')" width="110">
        <template #default="{ row }">{{ enumLabel('orderType', row.orderType) || row.orderTypeLabel }}</template>
      </el-table-column>
      <el-table-column prop="orderTitle" :label="t('workorder.orderTitle')" min-width="200" />
      <el-table-column prop="orderSource" :label="t('workorder.source')" width="100">
        <template #default="{ row }">
          {{ enumLabel('orderSource', row.orderSource) || row.orderSourceLabel || row.orderSource }}
        </template>
      </el-table-column>
      <el-table-column prop="orderStatus" :label="t('workorder.orderStatus')" width="110">
        <template #default="{ row }">{{ enumLabel('orderStatus', row.orderStatus) || row.orderStatusLabel }}</template>
      </el-table-column>
      <el-table-column prop="assignUserName" :label="t('workorder.assignee')" width="110">
        <template #default="{ row }">{{ row.assignUserName || '—' }}</template>
      </el-table-column>
      <el-table-column prop="slaStatus" label="SLA" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.responseOverdue || row.finishOverdue" type="danger" size="small">
             {{ t('workorder.overdue') }}
          </el-tag>
          <el-tag v-else type="success" size="small">{{ t('workorder.normal') }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" :label="t('workorder.created')" width="170" />
      <el-table-column :label="t('workorder.actions')" width="230" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.orderStatus === 'PENDING'" link type="warning"
                     @click="autoAssign(row)" data-testid="wo-autoassign">{{ t('workorder.autoAssign') }}</el-button>
          <el-button link type="primary" @click="act(row, 'accept')">{{ t('workorder.accept') }}</el-button>
          <el-button link type="success" @click="finish(row)">{{ t('workorder.finish') }}</el-button>
          <el-dropdown trigger="click" style="margin-left:8px">
            <el-button link type="primary">{{ t('workorder.more') }}</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="act(row, 'start')">{{ t('workorder.start') }}</el-dropdown-item>
                <el-dropdown-item @click="closeOrder(row)">{{ t('workorder.close') }}</el-dropdown-item>
                <el-dropdown-item @click="cancelOrder(row)">{{ t('workorder.cancelOrder') }}</el-dropdown-item>
                <el-dropdown-item @click="rejectOrder(row)">{{ t('workorder.reject') }}</el-dropdown-item>
                <el-dropdown-item @click="logs(row)">{{ t('workorder.logs') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />

    <el-drawer v-model="logVisible" :title="t('workorder.logTitle')" size="460px">
      <el-timeline>
        <el-timeline-item v-for="l in logList" :key="l.id" :timestamp="l.createTime">
          {{ l.action }} — {{ l.operatorName }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!logList.length" :description="t('workorder.noLogs')" />
    </el-drawer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { workOrderApi } from '@/api/modules'
import req from '@/api/request'

const { t } = useI18n()
const statuses = ['PENDING', 'ASSIGNED', 'ACCEPTED', 'PROCESSING', 'FINISHED',
  'CLOSED', 'CANCELLED']
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, orderStatus: '' })
const logVisible = ref(false)
const logList = ref([])

async function load() {
  loading.value = true
  try {
    const data = await workOrderApi.page({
      pageNum: query.pageNum, pageSize: query.pageSize,
      orderStatus: query.orderStatus || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}
function reload() { query.pageNum = 1; load() }

/** 巡检计划（物业管理）：列表 / 新建 / 执行到期 */
const saving = ref(false)
const plansVisible = ref(false)
const planFormVisible = ref(false)
const plans = ref([])
const pf = reactive({ planName: '', inspectType: 'SAFETY', frequency: 'MONTH',
  nextRunDate: '', assignUserName: '', remark: '' })

async function openPlans() {
  plansVisible.value = true
  await loadPlans()
}

async function loadPlans() {
  try {
    const d = await req.get('/ops/inspection-plans', { params: { pageNum: 1, pageSize: 100 } })
    plans.value = (d && d.rows) || []
  } catch (e) { plans.value = [] }
}

async function doCreatePlan() {
  if (!pf.planName) { ElMessage.warning('请填写计划名称'); return }
  saving.value = true
  try {
    await req.post('/ops/inspection-plans', { ...pf })
    ElMessage.success('计划已创建')
    planFormVisible.value = false
    await loadPlans()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '创建失败')
  } finally { saving.value = false }
}

async function runDue() {
  saving.value = true
  try {
    const r = await req.post('/ops/inspection-plans/run-due', {})
    ElMessage.success(`到期 ${r?.due || 0} 个，生成工单 ${r?.generated || 0} 个`)
    await loadPlans()
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '执行失败')
  } finally { saving.value = false }
}

async function act(row, action) {
  await workOrderApi[action](row.id)
  ElMessage.success('操作成功')
  load()
}
async function finish(row) {
  await workOrderApi.finish(row.id, { finishRemark: '现场处理完成' })
  ElMessage.success('工单已完成')
  load()
}
/** ActionCmd{operatorId, operatorName, content} */
async function orderAction(row, action, label, placeholder) {
  const { value } = await ElMessageBox.prompt(placeholder || '处理说明（可空）', label,
    { inputValue: '' })
  await workOrderApi[action](row.id, {
    operatorId: 1, operatorName: '管理员', content: value || label
  })
  ElMessage.success(label + '成功')
  load()
}

function closeOrder(row) { return orderAction(row, 'close', '关单', '关单说明（可空）') }
function cancelOrder(row) { return orderAction(row, 'cancel', '取消', '取消原因') }
function rejectOrder(row) { return orderAction(row, 'reject', '退回', '退回原因') }

async function logs(row) {
  logList.value = await workOrderApi.logs(row.id)
  logVisible.value = true
}

/** 自动派单：同组织服务岗在手工单最少者 */
async function autoAssign(row) {
  saving.value = true
  try {
    const r = await req.post(`/workorders/${row.id}/auto-assign`)
    ElMessage.success(`已派给 ${r?.assignUserName || '处理人'}`)
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '派单失败')
  } finally { saving.value = false }
}

/** 批量派单：处理当前所有待派单工单 */
async function autoAssignPending() {
  await ElMessageBox.confirm('将为所有待派单工单自动分配责任人，是否继续？',
    '确认批量派单', { type: 'warning' })
  saving.value = true
  try {
    const n = await req.post('/workorders/auto-assign-pending')
    ElMessage.success(n > 0 ? `已派单 ${n} 条` : '没有可派单的工单')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '批量派单失败')
  } finally { saving.value = false }
}
/** SLA 超时升级：标记超时工单并补派责任人 */
async function escalateOverdue() {
  saving.value = true
  try {
    const n = await req.post('/workorders/escalate-overdue')
    ElMessage.success(n > 0 ? `已升级 ${n} 条超时工单` : '暂无超时工单')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '超时升级失败')
  } finally { saving.value = false }
}
onMounted(load)
</script>
