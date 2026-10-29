<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">资金流水</h3>
      <el-radio-group v-model="tab" size="small" @change="onTab">
        <el-radio-button label="flow">资金流水</el-radio-button>
        <el-radio-button label="reconcile">对账单</el-radio-button>
        <el-radio-button label="payment">收款确认</el-radio-button>
      </el-radio-group>
      <div class="spacer" />
      <span class="muted" style="font-size:12px">
        核销 / 退款 / 补贴都会自动记账，形成完整资金流水
      </span>
    </div>

    <!-- ==================== 资金流水 ==================== -->
    <div v-show="tab === 'flow'">
      <div class="toolbar" style="margin-bottom:10px">
        <el-input v-model="keyword" placeholder="关键字" clearable style="width:170px"
                  @keyup.enter="reload" />
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button @click="resetQuery">清空</el-button>
        <span class="muted">共 {{ total }} 条</span>
      </div>
      <el-table :data="rows" v-loading="loading" border size="small" empty-text="暂无数据，可调整筛选条件或点击右上角新建">
        <el-table-column type="expand">
          <template #default="{ row }"><DetailView :row="row" /></template>
        </el-table-column>
        <el-table-column prop="flowNo" label="流水号" width="170" />
        <el-table-column prop="bizType" label="业务类型" width="130">
          <template #default="{ row }">{{ row.bizTypeLabel || enumLabel('bizType', row.bizType) }}</template>
        </el-table-column>
        <el-table-column prop="flowType" label="收支" width="100">
          <template #default="{ row }">{{ row.flowTypeLabel || enumLabel('flowType', row.flowType) }}</template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="110" />
        <el-table-column prop="flowTime" label="时间" width="170" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" :disabled="row.verifyStatus === 'VERIFIED'"
                       @click="doVerify(row)">核验</el-button>
            <el-button link @click="detail = row; show = true">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="pageSize" :current-page="pageNum"
                     @current-change="(p) => { pageNum = p; load() }" />
    </div>

    <!-- ==================== 对账单 ==================== -->
    <div v-show="tab === 'reconcile'">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="对账 = 系统收款 vs 渠道（微信/支付宝/银行）金额；有差异的对账单需人工处理后归档" />
      <div class="toolbar" style="margin-bottom:10px">
        <el-date-picker v-model="rq.dateRange" type="daterange" value-format="YYYY-MM-DD"
                        start-placeholder="开始日期" end-placeholder="结束日期"
                        style="width:250px" />
        <el-select v-model="rq.reconcileType" placeholder="对账类型" clearable style="width:130px">
          <el-option label="渠道对账" value="CHANNEL" />
          <el-option label="日终对账" value="DAILY" />
          <el-option label="手工对账" value="MANUAL" />
        </el-select>
        <el-select v-model="rq.status" placeholder="状态" clearable style="width:120px">
          <el-option label="一致" value="MATCHED" />
          <el-option label="有差异" value="DIFF" />
          <el-option label="已处理" value="HANDLED" />
        </el-select>
        <el-button type="primary" @click="loadReconciles">查询</el-button>
        <el-button @click="resetReconcile">清空</el-button>
        <el-button type="success" @click="openReconcile">新建对账</el-button>
        <span class="muted">共 {{ reconcileTotal }} 条</span>
      </div>

      <el-table :data="reconciles" v-loading="reconcileLoading" border size="small">
        <el-table-column prop="reconcileNo" label="对账号" width="180" />
        <el-table-column prop="reconcileDate" label="对账日期" width="120" />
        <el-table-column prop="reconcileType" label="类型" width="110">
          <template #default="{ row }">{{ enumLabel('reconcileType', row.reconcileType) }}</template>
        </el-table-column>
        <el-table-column prop="payChannel" label="渠道" width="110">
          <template #default="{ row }">{{ row.payChannel ? enumLabel('payChannel', row.payChannel) : '全部' }}</template>
        </el-table-column>
        <el-table-column prop="systemAmount" label="系统金额" width="120" />
        <el-table-column prop="channelAmount" label="渠道金额" width="120" />
        <el-table-column prop="diffAmount" label="差异金额" width="120">
          <template #default="{ row }">
            <span :class="{ danger: Number(row.diffAmount) !== 0 }">{{ row.diffAmount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="diffCount" label="差异笔数" width="100" />
        <el-table-column prop="reconcileStatus" label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="row.matched ? 'success'
              : (row.reconcileStatus === 'DIFF' ? 'danger' : 'info')">
              {{ row.reconcileStatusLabel || enumLabel('reconcileStatus', row.reconcileStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" :disabled="row.reconcileStatus !== 'DIFF'"
                       @click="doHandle(row)">处理差异</el-button>
            <el-button link @click="detail = row; show = true">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="reconcileTotal" :page-size="rq.pageSize"
                     :current-page="rq.pageNum"
                     @current-change="(p) => { rq.pageNum = p; loadReconciles() }" />
    </div>

    <!-- ==================== 收款确认 ==================== -->
    <div v-show="tab === 'payment'">
      <el-alert type="info" :closable="false" show-icon style="margin-bottom:10px"
                title="待支付的收款单需「确认收款」后才计入流水；确认后可在账单页核销到具体账单" />
      <div class="toolbar" style="margin-bottom:10px">
        <el-input v-model="pq.keyword" placeholder="收款号 / 缴费人" clearable
                  style="width:190px" @keyup.enter="loadPayments" />
        <el-select v-model="pq.status" placeholder="收款状态" clearable style="width:130px">
          <el-option label="待支付" value="PENDING" />
          <el-option label="成功" value="SUCCESS" />
          <el-option label="失败" value="FAILED" />
          <el-option label="已退款" value="REFUNDED" />
        </el-select>
        <el-button type="primary" @click="loadPayments">查询</el-button>
        <el-button @click="resetPayment">清空</el-button>
        <span class="muted">共 {{ paymentTotal }} 条</span>
      </div>

      <el-table :data="payments" v-loading="paymentLoading" border size="small">
        <el-table-column prop="paymentNo" label="收款号" width="180" />
        <el-table-column prop="payerName" label="缴费人" width="120">
          <template #default="{ row }">{{ row.payerName || row.personIdName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="payAmount" label="收款金额" width="110" />
        <el-table-column prop="payChannel" label="渠道" width="110">
          <template #default="{ row }">{{ enumLabel('payChannel', row.payChannel) }}</template>
        </el-table-column>
        <el-table-column prop="payTime" label="支付时间" width="170" />
        <el-table-column prop="payStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.payStatus === 'SUCCESS' ? 'success'
              : (row.payStatus === 'PENDING' ? 'warning' : 'info')">
              {{ row.payStatusLabel || enumLabel('payStatus', row.payStatus) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reconciledAmount" label="已核销" width="110" />
        <el-table-column prop="remainAmount" label="可核销余额" width="120" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" :disabled="row.payStatus !== 'PENDING'"
                       @click="doConfirm(row)">确认收款</el-button>
            <el-button link @click="detail = row; show = true">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="paymentTotal" :page-size="pq.pageSize"
                     :current-page="pq.pageNum"
                     @current-change="(p) => { pq.pageNum = p; loadPayments() }" />
    </div>

    <!-- 新建对账 -->
    <el-dialog v-model="reconcileVisible" title="新建对账" width="560px">
      <el-form :model="rf" label-width="120px">
        <el-form-item label="对账日期" required>
          <el-date-picker v-model="rf.reconcileDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item label="对账类型" required>
          <el-select v-model="rf.reconcileType" style="width:100%">
            <el-option label="渠道对账（按支付渠道）" value="CHANNEL" />
            <el-option label="日终对账（全渠道）" value="DAILY" />
            <el-option label="手工对账" value="MANUAL" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="rf.reconcileType !== 'DAILY'" label="支付渠道">
          <el-select v-model="rf.payChannel" clearable style="width:100%">
            <el-option label="微信" value="WECHAT" />
            <el-option label="支付宝" value="ALIPAY" />
            <el-option label="银行转账" value="BANK" />
            <el-option label="现金" value="CASH" />
          </el-select>
        </el-form-item>
        <el-form-item label="系统金额（选填）">
          <el-input v-model.number="rf.systemAmount"
                    placeholder="留空=按日期+渠道自动汇总" />
        </el-form-item>
        <el-form-item label="渠道金额" required>
          <el-input v-model.number="rf.channelAmount" placeholder="渠道对账单上的合计金额" />
        </el-form-item>
        <el-form-item label="差异笔数">
          <el-input-number v-model="rf.diffCount" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="差异明细链接">
          <el-input v-model="rf.diffDetailUrl" placeholder="选填，如渠道对账文件地址" />
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="系统金额留空时按「日期 + 渠道」汇总已确认收款；两者不一致时对账单状态为「有差异」" />
      <template #footer>
        <el-button @click="reconcileVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateReconcile">保存</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="show" title="明细（原始数据）" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>
</template>

<script setup>
/**
 * 资金：流水 / 对账单 / 收款确认。
 * 对账单与收款确认是资金闭环里原本缺失的界面（后端接口已就绪）。
 */
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/modules'
import req from '@/api/request'

const tab = ref('flow')
const show = ref(false)
const detail = ref(null)
const saving = ref(false)

// ---------------- 资金流水 ----------------
const loading = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')

async function load() {
  loading.value = true
  try {
    const d = await financeApi.cashflow({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}

function reload() { pageNum.value = 1; load() }
function resetQuery() { keyword.value = ''; pageNum.value = 1; load() }

/** 流水核验：与渠道核对后标记 */
async function doVerify(row) {
  await ElMessageBox.confirm('确认该笔流水已与渠道核对一致？', '核验流水', { type: 'warning' })
  await req.post(`/fin/cash-flows/${row.id}/verify`)
  ElMessage.success('已核验')
  load()
}

// ---------------- 对账单 ----------------
const reconciles = ref([])
const reconcileTotal = ref(0)
const reconcileLoading = ref(false)
const rq = reactive({ pageNum: 1, pageSize: 20, dateRange: null,
  reconcileType: undefined, status: undefined })

async function loadReconciles() {
  reconcileLoading.value = true
  try {
    const params = { pageNum: rq.pageNum, pageSize: rq.pageSize }
    if (rq.dateRange && rq.dateRange.length === 2) {
      params.dateFrom = rq.dateRange[0]
      params.dateTo = rq.dateRange[1]
    }
    if (rq.reconcileType) params.reconcileType = rq.reconcileType
    if (rq.status) params.status = rq.status
    const d = await financeApi.reconciles(params)
    reconciles.value = d.rows || []
    reconcileTotal.value = Number(d.total || 0)
  } catch (e) {
    reconciles.value = []; reconcileTotal.value = 0
  } finally { reconcileLoading.value = false }
}

function resetReconcile() {
  rq.dateRange = null; rq.reconcileType = undefined; rq.status = undefined
  rq.pageNum = 1
  loadReconciles()
}

const reconcileVisible = ref(false)
const rf = reactive({ reconcileDate: new Date().toISOString().slice(0, 10),
  reconcileType: 'CHANNEL', payChannel: 'WECHAT', systemAmount: null,
  channelAmount: null, diffCount: 0, diffDetailUrl: '' })

function openReconcile() {
  Object.assign(rf, { reconcileDate: new Date().toISOString().slice(0, 10),
    reconcileType: 'CHANNEL', payChannel: 'WECHAT', systemAmount: null,
    channelAmount: null, diffCount: 0, diffDetailUrl: '' })
  reconcileVisible.value = true
}

async function doCreateReconcile() {
  if (!rf.reconcileDate || !rf.channelAmount) {
    ElMessage.warning('对账日期与渠道金额为必填')
    return
  }
  saving.value = true
  try {
    const r = await req.post('/fin/reconciles', {
      reconcileDate: rf.reconcileDate,
      reconcileType: rf.reconcileType,
      payChannel: rf.reconcileType === 'DAILY' ? null : rf.payChannel,
      systemAmount: rf.systemAmount || null,
      channelAmount: rf.channelAmount,
      diffCount: rf.diffCount || 0,
      diffDetailUrl: rf.diffDetailUrl || null
    })
    ElMessage.success(`对账已生成：${r.reconcileNo}（差异 ${r.diffAmount}）`)
    reconcileVisible.value = false
    loadReconciles()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '对账生成失败')
  } finally { saving.value = false }
}

async function doHandle(row) {
  const { value } = await ElMessageBox.prompt(
    `处理差异（差异金额 ${row.diffAmount}，差异 ${row.diffCount} 笔）`,
    '处理对账差异',
    { inputPlaceholder: '处理说明，如「渠道手续费差异，已调整」',
      inputValidator: (v) => (v && v.trim() ? true : '请填写处理说明') })
  await req.post(`/fin/reconciles/${row.id}/handle`, { remark: value })
  ElMessage.success('已处理')
  loadReconciles()
}

// ---------------- 收款确认 ----------------
const payments = ref([])
const paymentTotal = ref(0)
const paymentLoading = ref(false)
const pq = reactive({ pageNum: 1, pageSize: 20, keyword: '', status: 'PENDING' })

async function loadPayments() {
  paymentLoading.value = true
  try {
    const d = await financeApi.payments({
      pageNum: pq.pageNum, pageSize: pq.pageSize,
      keyword: pq.keyword || undefined, status: pq.status || undefined
    })
    payments.value = d.rows || []
    paymentTotal.value = Number(d.total || 0)
  } catch (e) {
    payments.value = []; paymentTotal.value = 0
  } finally { paymentLoading.value = false }
}

function resetPayment() {
  pq.keyword = ''; pq.status = 'PENDING'; pq.pageNum = 1
  loadPayments()
}

async function doConfirm(row) {
  await ElMessageBox.confirm(
    `确认收款「${row.paymentNo}」金额 ${row.payAmount} 元已到账？确认后计入资金流水。`,
    '确认收款', { type: 'warning' })
  await req.post(`/fin/payments/${row.id}/confirm`)
  ElMessage.success('已确认收款')
  loadPayments()
}

function onTab() {
  if (tab.value === 'reconcile') loadReconciles()
  else if (tab.value === 'payment') loadPayments()
  else load()
}

onMounted(() => { load(); loadReconciles(); loadPayments() })
</script>

<style scoped>
.danger { color: #f56c6c; }
</style>
