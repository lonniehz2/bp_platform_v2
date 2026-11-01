<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('shortRent.title') }}</h3>
      <el-tag size="small" type="info">{{ t('miscPage.shortRentTip') }}</el-tag>
      <div class="spacer" />
      <el-input v-model="keyword" :placeholder="t('shortRent.keyword')" clearable
                style="width:170px" @keyup.enter="reload" />
      <el-button type="primary" @click="reload">{{ t('shortRent.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('shortRent.reset') }}</el-button>
      <el-button type="primary" plain @click="byHouseVisible = true">{{ t('shortRent.byHouse') }}</el-button>
      <el-button plain @click="nightsVisible = true">{{ t('shortRent.nights') }}</el-button>

    </div>

    <el-alert type="info" :closable="false" show-icon
              :title="t('misc3.shortTip')" style="margin-bottom:12px" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column type="expand">
        <template #default="{ row }"><DetailView :row="row" /></template>
      </el-table-column>
      <el-table-column prop="orderNo" :label="t('shortRent.no')" width="170" />
      <el-table-column prop="houseId" :label="t('shortRent.house')" width="120">
        <template #default="{ row }">{{ row.houseIdName || row.houseId }}</template>
      </el-table-column>
      <el-table-column prop="checkInTime" :label="t('shortRent.checkIn')" width="120" />
      <el-table-column prop="checkOutTime" :label="t('shortRent.checkOut')" width="120" />
      <el-table-column prop="orderStatus" :label="t('shortRent.status')" width="110">
        <template #default="{ row }">{{ row.orderStatusLabel || enumLabel('orderStatus', row.orderStatus) }}</template>
      </el-table-column>
      <el-table-column :label="t('shortRent.actions')" :width="ROWACTIONS ? 210 : 110" fixed="right">
        <template #default="{ row }">

          <el-button v-if="row.orderStatus === 'PENDING'" link type="primary"
                       @click="doConfirm(row)" data-testid="sr-confirm">{{ t('shortRent.confirm') }}</el-button>
            <el-button v-if="row.orderStatus === 'CONFIRMED'" link type="success"
                       @click="doCheckIn(row)" data-testid="sr-checkin">{{ t('shortRent.checkInAction') }}</el-button>
            <el-button v-if="row.orderStatus === 'CHECKED_IN'" link type="warning"
                       @click="doCheckOut(row)" data-testid="sr-checkout">{{ t('shortRent.checkOutAction') }}</el-button>
            <el-button v-if="row.orderStatus === 'CONFIRMED'" link
                       @click="doNoShow(row)">{{ t('shortRent.noShow') }}</el-button>
            <el-button v-if="row.orderStatus === 'CHECKED_OUT'" link type="primary"
                       @click="doPay(row)">{{ t('shortRent.collect') }}</el-button>
            <el-button link type="danger" @click="cancel(row)">{{ t('shortRent.cancel') }}</el-button>
          <el-button link @click="openDetail(row)">{{ t('shortRent.detail') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="pageSize" :current-page="pageNum"
                   @current-change="(p) => { pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { pageSize = s; pageNum = 1; load() }" />

    <!-- 写操作表单（字段按后端 Cmd 定义配置） -->
    <el-dialog v-model="formVisible" :title="formTitle" width="560px">
      <el-form :model="model" label-width="120px">
        <el-form-item v-for="f in fields" :key="f.key" :label="f.label">
          <el-input v-if="f.type === 'text'" v-model="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'textarea'" type="textarea" :rows="3"
                    v-model="model[f.key]" :placeholder="f.ph || ''" />
          <el-input v-else-if="f.type === 'number'" v-model.number="model[f.key]"
                    :placeholder="f.ph || ''" />
          <el-date-picker v-else-if="f.type === 'date'" v-model="model[f.key]"
                          type="date" value-format="YYYY-MM-DD" style="width:100%" />
          <el-select v-else-if="f.type === 'select'" v-model="model[f.key]"
                     style="width:100%">
            <el-option v-for="o in f.options" :key="o.value"
                       :label="o.label" :value="o.value" />
          </el-select>
          <el-switch v-else-if="f.type === 'bool'" v-model="model[f.key]" />
        </el-form-item>
      </el-form>
      <el-alert v-if="formNote" :closable="false" show-icon type="warning"
                :title="formNote" style="margin-top:8px" />
      <template #footer>
        <el-button @click="formVisible = false">{{ t('shortRent.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="submit">{{ t('shortRent.submit') }}</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="detailVisible" :title="t('shortRent.detail')" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
  </div>

    <!-- 按房源查当日订单 -->
    <el-dialog v-model="byHouseVisible" :title="t('shortRent.byHouseTitle')" width="760px">
      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <HouseSelect v-model="bh.houseId" width="260px" testid="sr-byhouse-house" />
        <el-date-picker v-model="bh.date" type="date" value-format="YYYY-MM-DD"
                        placeholder="日期" style="width:150px" />
        <el-button type="primary" :loading="bhLoading" @click="loadByHouse">{{ t('shortRent.search') }}</el-button>
      </div>

      <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px">
        <span class="muted" style="font-size:12px">可用性（按日期段）</span>
        <el-date-picker v-model="bh.checkIn" type="date" value-format="YYYY-MM-DD"
                        placeholder="入住" style="width:140px" />
        <el-date-picker v-model="bh.checkOut" type="date" value-format="YYYY-MM-DD"
                        placeholder="退房" style="width:140px" />
        <el-button plain :loading="avLoading" @click="checkAvailability">{{ t('shortRent.checkAvail') }}</el-button>
      </div>
      <el-alert v-if="av" :type="av.available ? 'success' : 'warning'" :closable="false"
                :title="(av.houseName || av.houseCode || '房源') + '：' + (av.available ? '可整段出租' : '不可整段出租')
                  + '（' + av.freeDays + '/' + av.days + ' 天可售）'"
                style="margin-bottom:10px" />
      <el-table :data="bhRows" size="small" border max-height="360">
        <el-table-column prop="orderNo" label="订单号" width="170" />
        <el-table-column prop="checkInTime" :label="t('shortRent.checkIn')" width="150" />
        <el-table-column prop="checkOutTime" :label="t('shortRent.checkOut')" width="150" />
        <el-table-column prop="orderStatusLabel" :label="t('shortRent.status')" width="110" />
        <el-table-column :label="t('shortRent.amount')" width="100" >
          <template #default="{ row }">{{ $money(row.totalAmount) }}</template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="byHouseVisible = false">{{ t('shortRent.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 住晚计算 -->
    <el-dialog v-model="nightsVisible" :title="t('shortRent.nightsTitle')" width="520px">
      <el-alert type="info" :closable="false" show-icon
                title="退房时刻必须晚于入住时刻；跨夜按自然夜计算。" />
      <el-form label-width="90px" style="margin-top:12px">
        <el-form-item label="入住">
          <el-date-picker v-model="ng.checkIn" type="datetime"
                          value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
        <el-form-item label="退房">
          <el-date-picker v-model="ng.checkOut" type="datetime"
                          value-format="YYYY-MM-DDTHH:mm:ss" style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert v-if="ngNights !== null" :type="ngNights > 0 ? 'success' : 'error'"
                :closable="false" :title="ngNights > 0 ? ('共 ' + ngNights + ' 晚') : '退房时间不合法'" />
      <template #footer>
        <el-button @click="nightsVisible = false">{{ t('shortRent.close') }}</el-button>
        <el-button type="primary" @click="calcNights">{{ t('shortRent.calc') }}</el-button>
      </template>
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import DetailView from '@/components/DetailView.vue'
import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { shortRentApi } from '@/api/modules'
import req from '@/api/request'
import HouseSelect from '@/components/HouseSelect.vue'

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const total = ref(0)
const pageNum = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const detailVisible = ref(false)
const detail = ref(null)

const byHouseVisible = ref(false)
const bh = reactive({ houseId: '', date: new Date().toISOString().slice(0, 10),
  checkIn: '', checkOut: '' })
const bhRows = ref([])
const av = ref(null)
const avLoading = ref(false)
const bhLoading = ref(false)
const nightsVisible = ref(false)
const ng = reactive({ checkIn: '', checkOut: '' })
const ngNights = ref(null)

async function checkAvailability() {
  if (!bh.houseId) { ElMessage.warning('请选择房源'); return }
  if (!bh.checkIn || !bh.checkOut) { ElMessage.warning('请选择入住与退房日期'); return }
  avLoading.value = true
  try {
    av.value = await req.get('/house-calendar/' + bh.houseId + '/availability',
      { params: { checkIn: bh.checkIn, checkOut: bh.checkOut } })
  } catch (e) {
    av.value = null
    ElMessage.error(e?.response?.data?.message || '查询失败')
  } finally { avLoading.value = false }
}

async function loadByHouse() {
  if (!bh.houseId) { ElMessage.warning('请选择房源'); return }
  bhLoading.value = true
  try {
    const d = await req.get('/short-rent-orders/by-house',
      { params: { houseId: bh.houseId, date: bh.date, pageNum: 1, pageSize: 50 } })
    bhRows.value = d.rows || []
  } catch (e) {
    bhRows.value = []
    ElMessage.error(e?.response?.data?.message || '查询失败')
  } finally { bhLoading.value = false }
}

async function calcNights() {
  if (!ng.checkIn || !ng.checkOut) { ElMessage.warning('请选择入住与退房时间'); return }
  try {
    ngNights.value = await req.get('/short-rent-orders/calc-nights',
      { params: { checkIn: ng.checkIn, checkOut: ng.checkOut } })
  } catch (e) {
    ngNights.value = null
    ElMessage.error(e?.response?.data?.message || '计算失败')
  }
}

const formVisible = ref(false)
const formTitle = ref('')
const formNote = ref('')
const fields = []
const model = reactive({})

// 必填字段（取自后端 Cmd 的 @NotNull）
const REQUIRED = []
let submitFn = null


async function load() {
  loading.value = true
  try {
    const data = await shortRentApi.page({
      pageNum: pageNum.value, pageSize: pageSize.value,
      keyword: keyword.value || undefined
    })
    rows.value = data.rows || data || []
    total.value = Number(data.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}

function reload() { pageNum.value = 1; load() }
function openDetail(row) { detail.value = row; detailVisible.value = true }

function openForm(title, fieldDefs, fn, preset = {}, note = '') {
  formTitle.value = title
  formNote.value = note
  Object.keys(model).forEach((k) => delete model[k])
  fieldDefs.forEach((f) => { model[f.key] = preset[f.key] ?? f.default ?? '' })
  submitFn = fn
  formVisible.value = true
}

/** 必填校验（字段级，依赖后端 Cmd 的 @NotNull 语义）。 */
function validateForm() {
  const missing = fields.filter((f) => REQUIRED.includes(f.key)
    && (model[f.key] === '' || model[f.key] === null || model[f.key] === undefined))
  if (missing.length) {
    ElMessage.warning('请填写：' + missing.map((f) => f.label).join('、'))
    return false
  }
  // 数字类基本合法性
  for (const f of fields) {
    if (f.type === 'number' && model[f.key] !== '' && model[f.key] !== null
        && Number.isNaN(Number(model[f.key]))) {
      ElMessage.warning(f.label + '必须是数字')
      return false
    }
  }
  return true
}

async function submit() {
  if (!validateForm()) return
  saving.value = true
  try {
    await submitFn({ ...model })
    ElMessage.success('操作成功')
    formVisible.value = false
    load()
  } catch (e) { /* 拦截器已提示 */ } finally { saving.value = false }
}

async function cancel(row) {
  const { value } = await ElMessageBox.prompt('请输入取消原因', '取消订单')
  await shortRentApi.cancel(row.id, value)
  ElMessage.success('已取消并释放房源')
  load()
}

function resetQuery() {
  keyword.value = ''
  pageNum.value = 1
  reload()
}


/** 前台动作：确认 / 入住 / 退房 / 未到 / 收款 */
async function doConfirm(row) {
  await shortRentApi.confirm(row.id)
  ElMessage.success('订单已确认')
  load()
}

async function doCheckIn(row) {
  await shortRentApi.checkIn(row.id)
  ElMessage.success('已办理入住')
  load()
}

async function doCheckOut(row) {
  let extra = '0'
  try {
    const r = await ElMessageBox.prompt('额外费用（如超时、损坏，无则填 0）', '办理退房', {
      inputValue: '0', inputPattern: /^\d+(\.\d{1,2})?$/,
      inputErrorMessage: '请输入数字'
    })
    extra = r.value
  } catch (e) { return }
  await shortRentApi.checkOut(row.id, Number(extra))
  ElMessage.success('已办理退房，房态已释放')
  load()
}

async function doNoShow(row) {
  await shortRentApi.noShow(row.id)
  ElMessage.success('已标记未到')
  load()
}

async function doPay(row) {
  let amount = String(row.payableAmount || row.roomAmount || 0)
  try {
    const r = await ElMessageBox.prompt('收款金额', '登记收款', {
      inputValue: amount, inputPattern: /^\d+(\.\d{1,2})?$/,
      inputErrorMessage: '请输入数字'
    })
    amount = r.value
  } catch (e) { return }
  await shortRentApi.pay(row.id, Number(amount))
  ElMessage.success('收款已登记')
  load()
}

onMounted(load)
</script>

<style scoped>
.raw { max-height: 420px; overflow: auto; background: #f5f7fa; padding: 10px;
  border-radius: 6px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }
</style>
