<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">工单与维保</h3>
      <el-select v-model="query.orderStatus" placeholder="状态" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
      </el-select>
      <div class="spacer" />
      <el-button type="warning" plain @click="openPlans" data-testid="inspection-plans">
        巡检计划
      </el-button>
      <el-button type="primary" @click="reload">刷新</el-button>
    </div>

    <!-- 巡检计划（物业）：按周期自动生成工单 -->
    <el-dialog v-model="plansVisible" title="巡检计划" width="900px">
      <div style="display:flex;gap:8px;margin-bottom:10px">
        <el-button type="success" size="small" @click="planFormVisible = true">新建计划</el-button>
        <el-button type="warning" size="small" :loading="saving" @click="runDue">
          执行到期计划
        </el-button>
        <div style="flex:1" />
        <span class="muted" style="font-size:12px;align-self:center">
          到期计划会按周期生成「巡检」类工单，并自动推进下次执行日
        </span>
      </div>
      <el-table :data="plans" size="small" border max-height="360">
        <el-table-column prop="planName" label="计划名称" min-width="160" />
        <el-table-column prop="inspectType" label="巡检类型" width="110">
          <template #default="{ row }">
            {{ { SAFETY: '安全', EQUIPMENT: '设备', CLEANING: '保洁', GREEN: '绿化' }[row.inspectType] || row.inspectType }}
          </template>
        </el-table-column>
        <el-table-column prop="frequency" label="周期" width="90">
          <template #default="{ row }">
            {{ { DAY: '每日', WEEK: '每周', MONTH: '每月' }[row.frequency] || row.frequency }}
          </template>
        </el-table-column>
        <el-table-column prop="nextRunDate" label="下次执行" width="120" />
        <el-table-column prop="assignUserName" label="负责人" width="110" />
        <el-table-column prop="planStatus" label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.planStatus === 'ENABLED' ? 'success' : 'info'">
              {{ row.planStatus === 'ENABLED' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 新建巡检计划 -->
    <el-dialog v-model="planFormVisible" title="新建巡检计划" width="520px">
      <el-form :model="pf" label-width="100px">
        <el-form-item label="计划名称" required>
          <el-input v-model="pf.planName" placeholder="如：1号楼月度安全巡检" />
        </el-form-item>
        <el-form-item label="巡检类型">
          <el-select v-model="pf.inspectType" style="width:100%">
            <el-option label="安全" value="SAFETY" />
            <el-option label="设备" value="EQUIPMENT" />
            <el-option label="保洁" value="CLEANING" />
            <el-option label="绿化" value="GREEN" />
          </el-select>
        </el-form-item>
        <el-form-item label="周期">
          <el-radio-group v-model="pf.frequency">
            <el-radio-button value="DAY">每日</el-radio-button>
            <el-radio-button value="WEEK">每周</el-radio-button>
            <el-radio-button value="MONTH">每月</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="首次执行">
          <el-date-picker v-model="pf.nextRunDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="负责人">
          <el-input v-model="pf.assignUserName" placeholder="可空" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="pf.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreatePlan">创建</el-button>
      </template>
    </el-dialog>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="orderNo" label="工单号" width="170" />
      <el-table-column prop="orderType" label="类型" width="110">
        <template #default="{ row }">{{ row.orderTypeLabel || enumLabel('orderType', row.orderType) }}</template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" />
      <el-table-column prop="priority" label="优先级" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.priority === 'URGENT' ? 'danger' : 'info'">
            {{ row.priority }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="orderStatus" label="状态" width="120">
        <template #default="{ row }">{{ row.orderStatusLabel || enumLabel('orderStatus', row.orderStatus) }}</template>
      </el-table-column>
      <el-table-column prop="slaOverdue" label="SLA" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.slaOverdue" type="danger" size="small">超时</el-tag>
          <span v-else class="muted">正常</span>
        </template>
      </el-table-column>
      <el-table-column prop="createTime" label="创建时间" width="170" />
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="act(row, 'accept')">接单</el-button>
          <el-button link type="primary" @click="act(row, 'start')">开始</el-button>
          <el-button link type="success" @click="finish(row)">完成</el-button>
          <el-button link @click="logs(row)">日志</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <el-drawer v-model="logVisible" title="工单日志" size="460px">
      <el-timeline>
        <el-timeline-item v-for="l in logList" :key="l.id" :timestamp="l.createTime">
          {{ l.action }} — {{ l.operatorName }}
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!logList.length" description="暂无日志" />
    </el-drawer>
  </div>
</template>

<script setup>
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { workOrderApi } from '@/api/modules'
import req from '@/api/request'

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
async function logs(row) {
  logList.value = await workOrderApi.logs(row.id)
  logVisible.value = true
}
onMounted(load)
</script>
