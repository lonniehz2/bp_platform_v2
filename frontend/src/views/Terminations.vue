<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">退租管理</h3>
      <el-tag size="small" type="info">过渡期 3 月 / 1.5 倍（可配）</el-tag>
      <div class="spacer" />
      <el-button type="success" @click="createVisible = true">发起退租</el-button>
      <el-button @click="load">刷新</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon
              title="违规清退会进入信用惩戒；年审退出自动生成的腾退单类型为 OTHER（不触发 5 年禁申）"
              style="margin-bottom:12px" />

    <FilterBar @search="resetAndLoad" @reset="resetQuery">
      <el-select v-model="tf.status" placeholder="退租状态" clearable style="width:160px"
                 data-testid="term-status">
        <el-option label="申请中" value="APPLYING" />
        <el-option label="审批中" value="APPROVING" />
        <el-option label="已批准" value="APPROVED" />
        <el-option label="已完成" value="COMPLETED" />
        <el-option label="已驳回" value="REJECTED" />
        <el-option label="已撤销" value="CANCELLED" />
      </el-select>
      <template #more>
        <el-input v-model="tf.contractId" placeholder="合同 ID" clearable style="width:200px" />
        <el-select v-model="tf.type" placeholder="退租类型" clearable style="width:160px">
          <el-option label="协商终止" value="AGREEMENT" />
          <el-option label="违约终止" value="BREACH" />
          <el-option label="到期终止" value="EXPIRE" />
        </el-select>
      </template>
    </FilterBar>

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }">
          <DetailView :row="row" />
        </template>
      </el-table-column>
      <el-table-column prop="terminationNo" label="退租单号" width="170" />
      <el-table-column prop="contractId" label="合同" width="130">
        <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
      </el-table-column>
      <el-table-column prop="terminationType" label="类型" width="120">
        <template #default="{ row }">{{ row.terminationTypeLabel || enumLabel('terminationType', row.terminationType) }}</template>
      </el-table-column>
      <el-table-column prop="planExitDate" label="计划退出" width="115" />
      <el-table-column prop="actualExitDate" label="实际退出" width="115" />
      <el-table-column prop="terminationStatus" label="状态" width="130">
        <template #default="{ row }">
          <el-tag size="small" :type="row.terminationStatus === 'COMPLETED' ? 'success'
            : (row.terminationStatus === 'REJECTED' ? 'danger' : 'warning')">
            {{ row.terminationStatusLabel || enumLabel('terminationStatus', row.terminationStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="330" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="approve(row)">审批</el-button>
          <el-button link @click="openInspect(row)">查验</el-button>
          <el-button link type="warning" @click="openSettle(row)">结算</el-button>
          <el-button link type="danger" @click="openEnforce(row)">强制腾退</el-button>
          <el-button link type="success" @click="openRelease(row)">释放房源</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }" />

    <!-- 发起退租 TerminationCreateCmd -->
    <el-dialog v-model="createVisible" title="发起退租" width="560px">
      <el-form :model="c" label-width="120px">
        <el-form-item label="合同ID"><el-input v-model="c.contractId" /></el-form-item>
        <el-form-item label="房源ID"><el-input v-model="c.houseId" /></el-form-item>
        <el-form-item label="人员ID"><PersonPicker v-model="c.personId" width="240px" testid="person-picker" /></el-form-item>
        <el-form-item label="退租类型">
          <el-select v-model="c.terminationType" style="width:100%">
            <el-option label="正常退租" value="NORMAL" />
            <el-option label="违规清退" value="EXPEL" />
            <el-option label="到期不续" value="EXPIRE" />
            <el-option label="换房退出" value="EXCHANGE" />
            <el-option label="其他" value="OTHER" />
          </el-select></el-form-item>
        <el-form-item label="计划退出日">
          <el-date-picker v-model="c.planExitDate" type="date"
                          value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="退出原因">
          <el-input v-model="c.exitReason" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="过渡期(月)">
          <el-input v-model.number="c.transitionMonths" placeholder="默认 3" /></el-form-item>
        <el-form-item label="过渡期租金倍率">
          <el-input v-model.number="c.transitionRentMultiplier" placeholder="默认 1.5" />
        </el-form-item>
        <el-form-item label="搬迁期(月)">
          <el-input v-model.number="c.relocationMonths" placeholder="成都上限 6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreate">提交</el-button>
      </template>
    </el-dialog>

    <!-- 查验 InspectCmd -->
    <el-dialog v-model="inspectVisible" title="退租查验" width="500px">
      <el-form :model="ins" label-width="120px">
        <el-form-item label="查验结论">
          <el-select v-model="ins.inspectStatus" style="width:100%">
            <el-option label="合格" value="PASS" />
            <el-option label="需维修" value="REPAIR" />
            <el-option label="有损坏" value="DAMAGED" />
          </el-select></el-form-item>
        <el-form-item label="查验说明">
          <el-input v-model="ins.inspectResult" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="损坏赔偿额">
          <el-input v-model.number="ins.damageAmount" /></el-form-item>
        <el-form-item label="查验照片URL">
          <el-input v-model="ins.inspectImages" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inspectVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doInspect">提交</el-button>
      </template>
    </el-dialog>

    <!-- 结算 SettleCmd -->
    <el-dialog v-model="settleVisible" title="退租结算" width="460px">
      <el-form :model="st" label-width="130px">
        <el-form-item label="押金退还额">
          <el-input v-model.number="st.depositRefund" /></el-form-item>
        <el-form-item label="欠费扣缴额">
          <el-input v-model.number="st.arrearsAmount" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="settleVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doSettle">确认结算</el-button>
      </template>
    </el-dialog>

    <!-- 强制腾退 EnforceCmd -->
    <el-dialog v-model="enforceVisible" title="强制腾退" width="520px">
      <el-form :model="en" label-width="130px">
        <el-form-item label="申请日期">
          <el-date-picker v-model="en.enforceApplyDate" type="date"
                          value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="受理法院"><el-input v-model="en.enforceCourt" /></el-form-item>
        <el-form-item label="公证书号"><el-input v-model="en.notaryNo" /></el-form-item>
        <el-form-item label="经办人">
          <el-input v-model="en.itemHandlerName" /></el-form-item>
        <el-form-item label="经办电话">
          <el-input v-model="en.itemHandlerPhone" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="enforceVisible = false">取消</el-button>
        <el-button type="danger" :loading="saving" @click="doEnforce">确认</el-button>
      </template>
    </el-dialog>

    <!-- 释放 ReleaseCmd -->
    <el-dialog v-model="releaseVisible" title="释放房源/撤销授权" width="420px">
      <el-form :model="rl" label-width="130px">
        <el-form-item label="释放房源">
          <el-switch v-model="rl.houseReleased" /></el-form-item>
        <el-form-item label="撤销门禁授权">
          <el-switch v-model="rl.grantRevoked" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="releaseVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRelease">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import DetailView from '@/components/DetailView.vue'
import FilterBar from '@/components/FilterBar.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { terminationApi } from '@/api/modules'
import req from '@/api/request'

const loading = ref(false)
const saving = ref(false)
const rows = ref([])
/** 列表筛选条件（后端 /terminations 支持 status / type / contractId） */
const tf = reactive({ status: '', type: '', contractId: '' })
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const current = ref(null)

const createVisible = ref(false)
const inspectVisible = ref(false)
const settleVisible = ref(false)
const enforceVisible = ref(false)
const releaseVisible = ref(false)

const c = reactive({ contractId: null, houseId: null, personId: null,
  terminationType: 'NORMAL', planExitDate: '', exitReason: '',
  transitionMonths: 3, transitionRentMultiplier: 1.5, relocationMonths: null })
const ins = reactive({ inspectStatus: 'PASS', inspectResult: '',
  damageAmount: null, inspectImages: '' })
const st = reactive({ depositRefund: null, arrearsAmount: null })
const en = reactive({ enforceApplyDate: '', enforceCourt: '', notaryNo: '',
  itemHandlerName: '', itemHandlerPhone: '' })
const rl = reactive({ houseReleased: true, grantRevoked: true })

async function load() {
  loading.value = true
  try {
    const d = await terminationApi.page({
      pageNum: pageNum.value, pageSize: pageSize.value,
      status: tf.status || undefined,
      type: tf.type || undefined,
      contractId: tf.contractId || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}

/** 查询：回到第 1 页再拉 */
function resetAndLoad() {
  pageNum.value = 1
  load()
}

/** 清空全部筛选条件 */
function resetQuery() {
  tf.status = ''
  tf.type = ''
  tf.contractId = ''
  resetAndLoad()
}

async function doCreate() {
  if (!c.contractId || !c.personId) {
    ElMessage.warning('合同与人员为必填'); return
  }
  saving.value = true
  try {
    await terminationApi.create({ ...c })
    ElMessage.success('退租单已创建')
    createVisible.value = false; load()
  } finally { saving.value = false }
}

async function approve(row) {
  await ElMessageBox.confirm('确认审批通过该退租单？', '审批', { type: 'warning' })
  await terminationApi.approve(row.id, {})
  ElMessage.success('已审批'); load()
}

function openInspect(row) { current.value = row; inspectVisible.value = true }
async function doInspect() {
  saving.value = true
  try {
    await req.post(`/terminations/${current.value.id}/inspect`, { ...ins })
    ElMessage.success('查验已提交')
    inspectVisible.value = false; load()
  } finally { saving.value = false }
}

function openSettle(row) { current.value = row; settleVisible.value = true }
async function doSettle() {
  saving.value = true
  try {
    await req.post(`/terminations/${current.value.id}/settle`, { ...st })
    ElMessage.success('结算完成')
    settleVisible.value = false; load()
  } finally { saving.value = false }
}

function openEnforce(row) { current.value = row; enforceVisible.value = true }
async function doEnforce() {
  saving.value = true
  try {
    await req.post(`/terminations/${current.value.id}/enforce`, { ...en })
    ElMessage.success('强制腾退已登记')
    enforceVisible.value = false; load()
  } finally { saving.value = false }
}

function openRelease(row) { current.value = row; releaseVisible.value = true }
async function doRelease() {
  saving.value = true
  try {
    await req.post(`/terminations/${current.value.id}/release`, { ...rl })
    ElMessage.success('房源与授权已释放')
    releaseVisible.value = false; load()
  } finally { saving.value = false }
}

// 待办中心「待处理退租」跳转过来时带 pending=1
if (/pending=1/.test(window.location.hash)) {
  tf.status = 'APPLYING'
}
onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
