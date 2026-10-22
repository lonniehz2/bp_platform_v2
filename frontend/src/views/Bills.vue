<template>
  <div>
    <div class="page-card">
      <div class="toolbar">
        <h3 style="margin:0">账单与缴费</h3>
        <el-select v-model="q.billStatus" placeholder="状态" clearable
                   style="width:140px" @change="reload">
          <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
        </el-select>
        <el-input v-model="q.billPeriod" placeholder="账期 2026-10" clearable
                  style="width:140px" @keyup.enter="reload" />
        <el-button type="primary" @click="reload">查询</el-button>
        <el-button @click="resetQuery">清空</el-button>
        <div class="spacer" />
        <el-button type="success" @click="genVisible = true">批量出账</el-button>
        <el-button type="warning" plain @click="openShared" data-testid="shared-bill">公摊分摊</el-button>
        <el-button type="primary" plain @click="openMeter" data-testid="meter-reading">抄表录入</el-button>
        <el-button @click="openPay">登记收款</el-button>
        <el-button @click="scanOverdue">扫描逾期</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border size="small">
        <el-table-column prop="billNo" label="账单号" width="165" />
        <el-table-column prop="payerName" label="缴费人" width="95" />
        <el-table-column prop="billPeriod" label="账期" width="95" />
        <el-table-column prop="billAmount" label="应收" width="90" />
        <el-table-column prop="paidAmount" label="已缴" width="90" />
        <el-table-column prop="waivedAmount" label="减免" width="85" />
        <el-table-column prop="payableAmount" label="待缴" width="90" />
        <el-table-column prop="dueDate" label="截止日" width="105" />
        <el-table-column prop="billStatusLabel" label="状态" width="95">
          <template #default="{ row }">
            <el-tag size="small" :type="row.overdueNow ? 'danger'
              : (row.billStatus === 'PAID' ? 'success' : 'info')">
              {{ row.billStatusLabel || row.billStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="overdueDays" label="逾期" width="70" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
            <el-button link type="primary" @click="openAllocate(row)">核销</el-button>
            <el-button link type="warning" @click="openWaive(row)">减免</el-button>
            <el-button link type="danger" @click="cancelBill(row)">取消</el-button>
            <el-button link @click="dunning(row)">催缴</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                     :total="total" :page-size="q.pageSize" :current-page="q.pageNum"
                     @current-change="(p) => { q.pageNum = p; load() }" />
    </div>

    <!-- 批量出账 -->
    <el-dialog v-model="genVisible" title="批量出账" width="500px">
      <el-form :model="g" label-width="120px">
        <el-form-item label="组织ID"><el-input v-model="g.orgId" /></el-form-item>
        <el-form-item label="账期">
          <el-input v-model="g.billPeriod" placeholder="2026-10" /></el-form-item>
        <el-form-item label="试算（不落库）">
          <el-switch v-model="g.dryRun" /></el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="会按计费项目的 7 种计费方式逐户计算；缺面积/抄表数据会明确报错并指明房源" />
      <template #footer>
        <el-button @click="genVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doGenerate">开始出账</el-button>
      </template>
    </el-dialog>

    <!-- 公摊费用分摊（物业） -->
    <el-dialog v-model="sharedVisible" title="公摊费用分摊出账" width="560px">
      <el-alert type="info" :closable="false" show-icon
                title="把公共区域总费用按面积或户数分摊到该范围内的在租房源，为每套生成一张账单"
                style="margin-bottom:12px" />
      <el-form :model="sf" label-width="110px">
        <el-form-item label="组织" required>
          <el-select v-model="sf.orgId" filterable style="width:100%" placeholder="选择组织/小区">
            <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName" :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="收费项目" required>
          <el-select v-model="sf.feeItemId" filterable style="width:100%">
            <el-option v-for="f in feeItems" :key="f.id"
                       :label="f.feeItemName || f.feeItemCode || f.id" :value="String(f.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="总金额" required>
          <el-input v-model="sf.totalAmount" type="number" placeholder="如 1200" />
        </el-form-item>
        <el-form-item label="分摊方式">
          <el-radio-group v-model="sf.allocateBy">
            <el-radio-button value="AREA">按建筑面积</el-radio-button>
            <el-radio-button value="HOUSE">按户数均摊</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="费用起始" required>
            <el-date-picker v-model="sf.periodStart" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="费用截止" required>
            <el-date-picker v-model="sf.periodEnd" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="账期" required>
            <el-input v-model="sf.billPeriod" placeholder="202610" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="到期日">
            <el-date-picker v-model="sf.dueDate" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="sharedVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doShared">开始分摊</el-button>
      </template>
    </el-dialog>

    <!-- 抄表录入（水电燃气按实际用量出账） -->
    <el-dialog v-model="meterVisible" title="抄表录入" width="860px">
      <el-alert type="info" :closable="false" show-icon
                title="录入本次读数后自动带出上次读数、用量与金额；确认无误再点「出账生成账单」"
                style="margin-bottom:12px" />
      <el-form :model="mf" label-width="96px" inline>
        <el-form-item label="房源">
          <el-select v-model="mf.houseId" filterable remote :remote-method="searchMeterHouse"
                     :loading="houseLoading" style="width:240px" placeholder="输入房号搜索">
            <el-option v-for="h in meterHouses" :key="h.id" :label="h.houseName" :value="String(h.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="收费项目">
          <el-select v-model="mf.feeItemId" filterable style="width:200px">
            <el-option v-for="f in meterItems" :key="f.id"
                       :label="`${f.itemName}（${f.unitPrice}/${f.unit || '单位'}）`"
                       :value="String(f.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="本次读数">
          <el-input v-model="mf.reading" type="number" style="width:140px" />
        </el-form-item>
        <el-form-item label="抄表日">
          <el-date-picker v-model="mf.readDate" type="date" value-format="YYYY-MM-DD"
                          style="width:150px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="doMeterRecord">录入读数</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="readings" size="small" border max-height="320" style="margin-top:8px">
        <el-table-column prop="readDate" label="抄表日" width="110" />
        <el-table-column prop="prevReading" label="上次读数" width="100" />
        <el-table-column prop="reading" label="本次读数" width="100" />
        <el-table-column prop="usageAmount" label="用量" width="90" />
        <el-table-column prop="unitPrice" label="单价" width="80" />
        <el-table-column prop="amount" label="金额" width="100" />
        <el-table-column prop="billStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.billStatus === 'BILLED' ? 'success' : 'warning'">
              {{ row.billStatus === 'BILLED' ? '已出账' : '待出账' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="row.billStatus === 'BILLED'"
                       @click="doMeterBill(row)">出账</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="meterVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 登记收款 PaymentCreateCmd -->
    <el-dialog v-model="payVisible" title="登记收款" width="520px">
      <el-form :model="p" label-width="110px">
        <el-form-item label="组织ID"><el-input v-model="p.orgId" /></el-form-item>
        <el-form-item label="人员ID"><PersonPicker v-model="p.personId" width="240px" testid="person-picker" /></el-form-item>
        <el-form-item label="缴费人"><el-input v-model="p.payerName" /></el-form-item>
        <el-form-item label="收款金额"><el-input v-model.number="p.payAmount" />
        </el-form-item>
        <el-form-item label="收款渠道">
          <el-select v-model="p.payChannel" style="width:100%">
            <el-option label="现金" value="CASH" />
            <el-option label="银行转账" value="BANK" />
            <el-option label="微信" value="WECHAT" />
            <el-option label="支付宝" value="ALIPAY" />
            <el-option label="POS" value="POS" />
          </el-select></el-form-item>
        <el-form-item label="交易流水号"><el-input v-model="p.tradeNo" /></el-form-item>
        <el-form-item label="来源不明">
          <el-switch v-model="p.unknownFlag" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="p.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="payVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doPay">确认收款</el-button>
      </template>
    </el-dialog>

    <!-- 核销 AllocateCmd -->
    <el-dialog v-model="allocVisible" title="账单核销" width="480px">
      <el-alert type="info" :closable="false" show-icon
                title="三重上限：不超收款单余额、不超账单应付、已缴账单不可再核销" />
      <el-form :model="a" label-width="110px" style="margin-top:12px">
        <el-form-item label="账单号">
          <el-input :model-value="current?.billNo" disabled /></el-form-item>
        <el-form-item label="账单待缴">
          <el-input :model-value="current?.payableAmount" disabled /></el-form-item>
        <el-form-item label="收款单ID"><el-input v-model="a.paymentId" />
        </el-form-item>
        <el-form-item label="核销金额">
          <el-input v-model.number="a.amount" placeholder="留空=全部待缴" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="allocVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doAllocate">确认核销</el-button>
      </template>
    </el-dialog>

    <!-- 减免 WaiveCmd -->
    <el-dialog v-model="waiveVisible" title="账单减免" width="460px">
      <el-form :model="w" label-width="110px">
        <el-form-item label="账单号">
          <el-input :model-value="current?.billNo" disabled /></el-form-item>
        <el-form-item label="减免金额">
          <el-input v-model.number="w.waiveAmount" placeholder="留空=全部待缴" /></el-form-item>
        <el-form-item label="减免原因">
          <el-input v-model="w.reason" type="textarea" :rows="3" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="waiveVisible = false">取消</el-button>
        <el-button type="warning" :loading="saving" @click="doWaive">确认减免</el-button>
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
import PersonPicker from '@/components/PersonPicker.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/modules'
import req from '@/api/request'

const statuses = ['UNPAID', 'PARTIAL', 'PAID', 'OVERDUE', 'WAIVED', 'CANCELLED']
const loading = ref(false)
const saving = ref(false)

/** 抄表录入（METER 类收费） */
const meterVisible = ref(false)
const meterItems = ref([])
const meterHouses = ref([])
const houseLoading = ref(false)
const readings = ref([])
const mf = reactive({ houseId: '', feeItemId: '', reading: 0, readDate: '' })

async function openMeter() {
  meterVisible.value = true
  mf.readDate = new Date().toISOString().slice(0, 10)
  if (!meterItems.value.length) {
    try {
      const fi = await financeApi.feeItems({ pageNum: 1, pageSize: 100 })
      meterItems.value = ((fi && fi.rows) || []).filter((x) => x.calcMode === 'METER')
    } catch (e) { /* 忽略 */ }
  }
  await searchMeterHouse('')
  await loadReadings()
}

async function searchMeterHouse(kw) {
  houseLoading.value = true
  try {
    const d = await financeApi.houses({ pageNum: 1, pageSize: 20, keyword: kw || undefined })
    meterHouses.value = (d && d.rows) || []
  } finally { houseLoading.value = false }
}

async function loadReadings() {
  try {
    const d = await financeApi.meterList({ pageNum: 1, pageSize: 50, houseId: mf.houseId || undefined })
    readings.value = (d && d.rows) || []
  } catch (e) { readings.value = [] }
}

async function doMeterRecord() {
  if (!mf.houseId || !mf.feeItemId || mf.reading === '' || mf.reading === null) {
    ElMessage.warning('请选择房源、收费项目并填写读数'); return
  }
  saving.value = true
  try {
    const r = await financeApi.meterRecord({
      houseId: mf.houseId, feeItemId: mf.feeItemId,
      reading: Number(mf.reading), readDate: mf.readDate || undefined
    })
    ElMessage.success(`已录入：用量 ${r?.usageAmount ?? '-'}，金额 ${r?.amount ?? '-'}`)
    await loadReadings()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '录入失败')
  } finally { saving.value = false }
}

async function doMeterBill(row) {
  saving.value = true
  try {
    const b = await req.post(`/fin/meter-readings/${row.id}/bill`, {})
    ElMessage.success(`已出账：${b?.billNo || ''}，应收 ${b?.payableAmount ?? ''}`)
    await loadReadings()
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '出账失败')
  } finally { saving.value = false }
}
const rows = ref([])
const total = ref(0)
const q = reactive({ pageNum: 1, pageSize: 20, billStatus: '', billPeriod: '' })
const current = ref(null)

const genVisible = ref(false)
const g = reactive({ orgId: 1, billPeriod: '', dryRun: true })

/** 公摊分摊（物业管理） */
const sharedVisible = ref(false)
const orgOptions = ref([])
const feeItems = ref([])
const sf = reactive({ orgId: '', feeItemId: '', totalAmount: 0, allocateBy: 'AREA',
  periodStart: '', periodEnd: '', billPeriod: '', dueDate: '' })

async function openShared() {
  sharedVisible.value = true
  try {
    const org = await financeApi.orgs({ pageNum: 1, pageSize: 100 })
    orgOptions.value = (org && org.rows) || []
  } catch (e) { /* 组织加载失败不阻断 */ }
  try {
    const fi = await financeApi.feeItems({ pageNum: 1, pageSize: 100 })
    feeItems.value = (fi && fi.rows) || []
  } catch (e) { /* 收费项目加载失败不阻断 */ }
}

async function doShared() {
  if (!sf.orgId || !sf.feeItemId || !sf.totalAmount) {
    ElMessage.warning('请填写组织、收费项目与总金额'); return
  }
  if (!sf.periodStart || !sf.periodEnd || !sf.billPeriod) {
    ElMessage.warning('请填写费用起止与账期'); return
  }
  saving.value = true
  try {
    const r = await financeApi.generateShared({
      orgId: sf.orgId, feeItemId: sf.feeItemId, totalAmount: Number(sf.totalAmount),
      allocateBy: sf.allocateBy, periodStart: sf.periodStart, periodEnd: sf.periodEnd,
      billPeriod: sf.billPeriod, dueDate: sf.dueDate || undefined
    })
    ElMessage.success(`已生成 ${r?.created || 0} 张分摊账单（跳过 ${r?.skipped || 0} 户无在租合同）`)
    sharedVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '分摊失败')
  } finally { saving.value = false }
}

const payVisible = ref(false)
const p = reactive({ orgId: 1, personId: null, payerName: '', payAmount: null,
  payChannel: 'CASH', tradeNo: '', unknownFlag: 0, remark: '' })

const allocVisible = ref(false)
const a = reactive({ paymentId: null, amount: null })

const waiveVisible = ref(false)
const w = reactive({ waiveAmount: null, reason: '' })

async function load() {
  loading.value = true
  try {
    const d = await financeApi.bills({
      pageNum: q.pageNum, pageSize: q.pageSize,
      billStatus: q.billStatus || undefined,
      billPeriod: q.billPeriod || undefined
    })
    rows.value = d.rows || []
    total.value = Number(d.total || 0)
  } finally { loading.value = false }
}
function reload() { q.pageNum = 1; load() }

async function doGenerate() {
  saving.value = true
  try {
    const r = await financeApi.generate({ ...g })
    ElMessage.success('出账完成：生成 ' + (r?.generated ?? r?.count ?? '-') + ' 张')
    genVisible.value = false; load()
  } finally { saving.value = false }
}

function openPay() { payVisible.value = true }
async function doPay() {
  if (!p.payAmount || p.payAmount <= 0) { ElMessage.warning('收款金额必须大于 0'); return }
  saving.value = true
  try {
    await financeApi.createPayment({ ...p })
    ElMessage.success('收款已登记')
    payVisible.value = false
  } finally { saving.value = false }
}

function openAllocate(row) {
  current.value = row; a.paymentId = null; a.amount = null
  allocVisible.value = true
}
async function doAllocate() {
  if (!a.paymentId) { ElMessage.warning('请填写收款单ID'); return }
  saving.value = true
  try {
    await financeApi.allocate(a.paymentId, current.value.id, a.amount)
    ElMessage.success('核销成功')
    allocVisible.value = false; load()
  } finally { saving.value = false }
}

function openWaive(row) {
  current.value = row; w.waiveAmount = null; w.reason = ''
  waiveVisible.value = true
}
async function doWaive() {
  if (!w.reason) { ElMessage.warning('请填写减免原因'); return }
  saving.value = true
  try {
    await financeApi.waive(current.value.id, { ...w })
    ElMessage.success('减免成功')
    waiveVisible.value = false; load()
  } finally { saving.value = false }
}

async function cancelBill(row) {
  const { value } = await ElMessageBox.prompt('请输入取消原因', '取消账单')
  await financeApi.cancelBill(row.id, value)
  ElMessage.success('账单已取消'); load()
}

async function dunning(row) {
  await financeApi.arrears({ billId: row.id })
  ElMessage.success('已发起催缴（可在催缴管理查看）')
}

async function scanOverdue() {
  await financeApi.scanOverdue()
  ElMessage.success('逾期扫描完成'); load()
}

const q0 = JSON.parse(JSON.stringify(q))
function resetQuery() {
  Object.assign(q, q0)
  reload()
}

onMounted(load)
</script>
