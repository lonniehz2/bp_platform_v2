# -*- coding: utf-8 -*-
"""生成前端页面：Contracts / Bills / Reports / Devices / AccessRecords"""
import io
import os

BASE = r'D:\Work\业务平台开发\frontend'
F = {}

F['src/views/Contracts.vue'] = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <el-input v-model="query.contractNo" placeholder="合同号" clearable
                style="width:180px" @keyup.enter="load" />
      <el-select v-model="query.contractStatus" placeholder="状态" clearable
                 style="width:150px" @change="load">
        <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="contractNo" label="合同号" width="170" />
      <el-table-column prop="lesseeName" label="承租人" width="100" />
      <el-table-column prop="houseAddress" label="房屋地址" min-width="180" />
      <el-table-column prop="leaseStart" label="起租" width="110" />
      <el-table-column prop="leaseEnd" label="止租" width="110" />
      <el-table-column prop="monthlyRent" label="月租金" width="100" />
      <el-table-column prop="contractStatusLabel" label="状态" width="100">
        <template #default="{ row }">
          <el-tag size="small" :type="row.expiringSoon ? 'warning' : 'info'">
            {{ row.contractStatusLabel || row.contractStatus }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="daysToExpire" label="距到期(天)" width="110" />
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <el-drawer v-model="detailVisible" title="合同详情" size="520px">
      <el-descriptions v-if="detail" :column="1" border size="small">
        <el-descriptions-item label="合同号">{{ detail.contractNo }}</el-descriptions-item>
        <el-descriptions-item label="类型">{{ detail.contractType }}</el-descriptions-item>
        <el-descriptions-item label="承租人">
          {{ detail.lesseeName }} / {{ detail.lesseePhone }}
        </el-descriptions-item>
        <el-descriptions-item label="证件（脱敏）">{{ detail.lesseeIdCardMask }}</el-descriptions-item>
        <el-descriptions-item label="房屋">{{ detail.houseAddress }}（{{ detail.houseArea }}㎡）</el-descriptions-item>
        <el-descriptions-item label="租期">
          {{ detail.leaseStart }} ~ {{ detail.leaseEnd }}（{{ detail.leaseMonths }} 月）
        </el-descriptions-item>
        <el-descriptions-item label="月租金">{{ detail.monthlyRent }}</el-descriptions-item>
        <el-descriptions-item label="押金">{{ detail.depositAmount }}</el-descriptions-item>
        <el-descriptions-item label="补贴">{{ detail.subsidyAmount }}</el-descriptions-item>
        <el-descriptions-item label="实付">{{ detail.actualPay }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ detail.contractStatusLabel }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { contractApi } from '@/api/modules'

const statuses = ['DRAFT', 'PENDING_SIGN', 'EFFECTIVE', 'CHANGING', 'TERMINATED', 'EXPIRED']
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, contractNo: '', contractStatus: '' })

const detailVisible = ref(false)
const detail = ref(null)

async function load() {
  loading.value = true
  try {
    const data = await contractApi.page({
      pageNum: query.pageNum, pageSize: query.pageSize,
      contractStatus: query.contractStatus || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}

async function openDetail(row) {
  detail.value = await contractApi.get(row.id)
  detailVisible.value = true
}

onMounted(load)
</script>
'''

F['src/views/Bills.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="query.billStatus" placeholder="账单状态" clearable
                   style="width:150px" @change="load">
          <el-option v-for="s in statuses" :key="s" :label="s" :value="s" />
        </el-select>
        <el-input v-model="query.billPeriod" placeholder="账期如 2026-10" clearable
                  style="width:160px" @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <div class="spacer" />
        <el-button type="success" @click="genVisible = true">批量出账</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="billNo" label="账单号" width="170" />
        <el-table-column prop="payerName" label="缴费人" width="100" />
        <el-table-column prop="billPeriod" label="账期" width="100" />
        <el-table-column prop="billAmount" label="应收" width="100" />
        <el-table-column prop="paidAmount" label="已缴" width="100" />
        <el-table-column prop="payableAmount" label="待缴" width="100" />
        <el-table-column prop="dueDate" label="截止日" width="110" />
        <el-table-column prop="billStatusLabel" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small"
                    :type="row.overdueNow ? 'danger' : (row.billStatus === 'PAID' ? 'success' : 'info')">
              {{ row.billStatusLabel || row.billStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="overdueDays" label="逾期天数" width="100" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openAllocate(row)">核销</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }" />
    </div>

    <!-- 核销 -->
    <el-dialog v-model="allocateVisible" title="账单核销" width="480px">
      <el-alert type="info" :closable="false" show-icon
                title="核销受三重上限约束：不得超过收款单余额、不得超过账单应付、已缴账单不可再核销" />
      <el-form :model="allocateForm" label-width="110px" style="margin-top:12px">
        <el-form-item label="账单号">
          <el-input :model-value="currentBill?.billNo" disabled />
        </el-form-item>
        <el-form-item label="账单待缴">
          <el-input :model-value="currentBill?.payableAmount" disabled />
        </el-form-item>
        <el-form-item label="收款单ID">
          <el-input v-model.number="allocateForm.paymentId" />
        </el-form-item>
        <el-form-item label="核销金额">
          <el-input v-model.number="allocateForm.amount" placeholder="留空=核销全部待缴" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="allocateVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doAllocate">确认核销</el-button>
      </template>
    </el-dialog>

    <!-- 批量出账 -->
    <el-dialog v-model="genVisible" title="批量出账" width="480px">
      <el-form :model="genForm" label-width="110px">
        <el-form-item label="组织ID">
          <el-input v-model.number="genForm.orgId" />
        </el-form-item>
        <el-form-item label="账期">
          <el-input v-model="genForm.billPeriod" placeholder="2026-10" />
        </el-form-item>
        <el-form-item label="试算">
          <el-switch v-model="genForm.dryRun" />
          <span class="muted" style="margin-left:8px">开启只试算不落库</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="genVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doGenerate">开始出账</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { financeApi } from '@/api/modules'

const statuses = ['UNPAID', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED']
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({ pageNum: 1, pageSize: 20, billStatus: '', billPeriod: '' })

const allocateVisible = ref(false)
const currentBill = ref(null)
const allocateForm = reactive({ paymentId: null, amount: null })

const genVisible = ref(false)
const genForm = reactive({ orgId: 1, billPeriod: '', dryRun: true })

async function load() {
  loading.value = true
  try {
    const data = await financeApi.bills({
      pageNum: query.pageNum, pageSize: query.pageSize,
      billStatus: query.billStatus || undefined,
      billPeriod: query.billPeriod || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}

function openAllocate(row) {
  currentBill.value = row
  allocateForm.paymentId = null
  allocateForm.amount = null
  allocateVisible.value = true
}

async function doAllocate() {
  saving.value = true
  try {
    await financeApi.allocate(allocateForm.paymentId, currentBill.value.id,
      allocateForm.amount)
    ElMessage.success('核销成功')
    allocateVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function doGenerate() {
  saving.value = true
  try {
    const res = await financeApi.generate({ ...genForm })
    ElMessage.success(`出账完成：生成 ${res?.generated ?? res?.count ?? '-'} 张`)
    genVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
'''

F['src/views/Reports.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-select v-model="reportCode" placeholder="选择报表" style="width:220px"
                   @change="onQuery">
          <el-option v-for="r in reports" :key="r.reportCode"
                     :label="r.reportName" :value="r.reportCode" />
        </el-select>
        <el-button type="primary" @click="onQuery">查询</el-button>
        <div class="spacer" />
        <el-button type="success" :loading="exporting" @click="onExport">
          <el-icon><Download /></el-icon>导出 CSV
        </el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column v-for="c in columns" :key="c.key"
                         :prop="c.key" :label="c.title" show-overflow-tooltip />
        <el-table-column v-if="!columns.length" label="提示">
          <template #default>请选择报表后查询</template>
        </el-table-column>
      </el-table>

      <div class="muted" style="margin-top:10px">{{ summary }}</div>
    </div>

    <div class="page-card">
      <h4 style="margin:0 0 12px">导出任务</h4>
      <el-table :data="tasks" border size="small">
        <el-table-column prop="taskNo" label="任务号" width="180" />
        <el-table-column prop="fileName" label="文件名" min-width="220" />
        <el-table-column prop="rowCount" label="行数" width="90" />
        <el-table-column prop="taskStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.taskStatus === 'SUCCESS' ? 'success' : 'info'">
              {{ row.taskStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <el-button link type="primary" @click="preview(row)">预览内容</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="previewVisible" title="导出文件内容（前 4000 字符）" width="760px">
      <pre class="csv-preview">{{ previewText }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { rptApi } from '@/api/modules'

const reports = ref([])
const reportCode = ref('HOUSE_LEDGER')
const columns = ref([])
const rows = ref([])
const summary = ref('')
const loading = ref(false)
const exporting = ref(false)

const tasks = ref([])
const previewVisible = ref(false)
const previewText = ref('')

async function loadReports() {
  reports.value = await rptApi.reports()
}

async function onQuery() {
  if (!reportCode.value) return
  loading.value = true
  try {
    const data = await rptApi.query({ reportCode: reportCode.value, pageNum: 1, pageSize: 100 })
    columns.value = data.columns || []
    rows.value = data.rows || []
    summary.value = data.summary || ''
  } finally {
    loading.value = false
  }
}

async function onExport() {
  if (!reportCode.value) return
  exporting.value = true
  try {
    const task = await rptApi.export({ reportCode: reportCode.value })
    ElMessage.success(`导出完成：${task.fileName}（${task.rowCount} 行）`)
    tasks.value.unshift(task)
  } finally {
    exporting.value = false
  }
}

async function preview(row) {
  previewText.value = await rptApi.taskContent(row.id)
  previewVisible.value = true
}

onMounted(async () => {
  await loadReports()
  await onQuery()
})
</script>

<style scoped>
.csv-preview {
  max-height: 460px;
  overflow: auto;
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre;
}
</style>
'''

F['src/views/Devices.vue'] = '''<template>
  <div class="page-card">
    <div class="toolbar">
      <el-input v-model="query.houseId" placeholder="房源ID" clearable
                style="width:160px" @keyup.enter="load" />
      <el-button type="primary" @click="load">查询</el-button>
      <div class="spacer" />
      <span class="muted">设备接口按房源维度查询（与 IoT 平台门锁绑定）</span>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="id" label="ID" width="150" />
      <el-table-column prop="lockId" label="门锁ID" width="180" />
      <el-table-column prop="deviceMac" label="MAC" width="160" />
      <el-table-column prop="spaceId" label="空间" width="120" />
      <el-table-column prop="bindStatus" label="绑定状态" width="110" />
      <el-table-column prop="createTime" label="绑定时间" width="170" />
    </el-table>
    <el-empty v-if="!loading && !rows.length" description="暂无设备数据（需先绑定门锁）" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { devApi } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const query = reactive({ houseId: '' })

async function load() {
  loading.value = true
  try {
    const data = await devApi.devices({
      pageNum: 1, pageSize: 50, houseId: query.houseId || undefined
    })
    rows.value = data.rows || data || []
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
'''

F['src/views/AccessRecords.vue'] = '''<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <el-input v-model="query.houseId" placeholder="房源ID" clearable
                  style="width:150px" @keyup.enter="load" />
        <el-input v-model="query.personId" placeholder="人员ID" clearable
                  style="width:150px" @keyup.enter="load" />
        <el-checkbox v-model="query.abnormalOnly">只看异常</el-checkbox>
        <el-button type="primary" @click="load">查询</el-button>
        <div class="spacer" />
        <el-button @click="openIdle">
          <el-icon><Warning /></el-icon>空置判定
        </el-button>
        <el-button @click="openRatio">不可信占比</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="openTime" label="开门时间" width="170" />
        <el-table-column prop="openTypeName" label="方式" width="100" />
        <el-table-column prop="houseId" label="房源" width="110" />
        <el-table-column prop="personId" label="人员" width="110" />
        <el-table-column prop="lockId" label="门锁" width="170" />
        <el-table-column prop="trusted" label="可信" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.trusted ? 'success' : 'warning'">
              {{ row.trusted ? '可信' : '不可信' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="abnormal" label="异常" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.abnormal" type="danger" size="small">异常</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="abnormalType" label="异常类型" width="120" />
        <el-table-column label="轨迹" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openTrace(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="query.pageSize"
                     :current-page="query.pageNum"
                     @current-change="(p) => { query.pageNum = p; load() }" />
    </div>

    <el-dialog v-model="traceVisible" title="行为轨迹" width="640px">
      <el-alert type="info" :closable="false" show-icon :title="trace?.summary || ''" />
      <el-timeline style="margin-top:14px;max-height:420px;overflow:auto">
        <el-timeline-item v-for="t in trace?.timeline || []" :key="t.id"
                          :timestamp="t.openTime" placement="top"
                          :type="t.abnormal ? 'danger' : 'primary'">
          {{ t.openTypeName }} — 房源 {{ t.houseId }}
          <span v-if="t.abnormal" class="muted">（{{ t.abnormalType }}）</span>
        </el-timeline-item>
      </el-timeline>
    </el-dialog>

    <el-dialog v-model="idleVisible" title="空置判定" width="640px">
      <el-alert type="warning" :closable="false" show-icon
                title="连续无开门天数超过阈值即判定疑似空置，可作为「长期空置」违规的客观依据" />
      <el-table :data="idleList" border size="small" style="margin-top:12px">
        <el-table-column prop="houseId" label="房源" width="120" />
        <el-table-column prop="lastOpenTime" label="最近开门" width="180" />
        <el-table-column prop="idleDays" label="连续天数" width="110" />
        <el-table-column prop="suspectIdle" label="疑似空置" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.suspectIdle ? 'danger' : 'success'">
              {{ row.suspectIdle ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="说明" min-width="200" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="ratioVisible" title="不可信开门占比（考核指标）" width="420px">
      <el-descriptions :column="1" border size="small">
        <el-descriptions-item label="总开门次数">{{ ratio.total }}</el-descriptions-item>
        <el-descriptions-item label="不可信次数">{{ ratio.untrusted }}</el-descriptions-item>
        <el-descriptions-item label="占比">{{ ratio.untrustedRatio }}%</el-descriptions-item>
        <el-descriptions-item label="阈值">{{ ratio.threshold }}%</el-descriptions-item>
        <el-descriptions-item label="是否达标">
          <el-tag :type="ratio.pass ? 'success' : 'danger'" size="small">
            {{ ratio.pass ? '达标' : '超标' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { devApi } from '@/api/modules'

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({
  pageNum: 1, pageSize: 20, houseId: '', personId: '', abnormalOnly: false
})

const traceVisible = ref(false)
const trace = ref(null)
const idleVisible = ref(false)
const idleList = ref([])
const ratioVisible = ref(false)
const ratio = ref({})

async function load() {
  loading.value = true
  try {
    const data = await devApi.accessRecords({
      pageNum: query.pageNum, pageSize: query.pageSize,
      houseId: query.houseId || undefined,
      personId: query.personId || undefined,
      abnormalOnly: query.abnormalOnly || undefined
    })
    rows.value = data.rows || []
    total.value = Number(data.total || 0)
  } finally {
    loading.value = false
  }
}

async function openTrace(row) {
  trace.value = row.houseId
    ? await devApi.traceByHouse(row.houseId)
    : await devApi.traceByPerson(row.personId)
  traceVisible.value = true
}

async function openIdle() {
  idleList.value = await devApi.idle({ idleDays: 30 })
  idleVisible.value = true
}

async function openRatio() {
  ratio.value = await devApi.untrustedRatio()
  ratioVisible.value = true
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
