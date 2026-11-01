<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('change.title') }}</h3>
      <el-tag size="small" type="info">{{ t('misc2.changeTag') }}</el-tag>
      <div class="spacer" />
      <el-select v-model="query.changeStatus" :placeholder="t('change.status')" clearable
                 style="width:150px" @change="reload">
        <el-option v-for="s in statuses" :key="s" :label="enumLabel(null, s)" :value="s" />
      </el-select>
      <el-button type="primary" @click="reload">{{ t('change.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('change.reset') }}</el-button>
    </div>

    <el-table :data="rows" v-loading="loading" border size="small" :empty-text="t('misc.emptyDefault')">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div style="display:flex;gap:24px;padding:8px 12px">
            <div style="flex:1"><b>变更前</b><div class="kv">{{ beforeText(row) }}</div></div>
            <div style="flex:1"><b>变更后</b><div class="kv">{{ afterText(row) }}</div></div>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="changeNo" :label="t('change.no')" width="170" />
      <el-table-column prop="houseName" :label="t('change.house')" width="150" />
      <el-table-column prop="lesseeName" :label="t('change.lessee')" width="110" />
      <el-table-column prop="contractId" :label="t('change.contract')" width="200">
        <template #default="{ row }">{{ row.contractIdName || row.contractId }}</template>
      </el-table-column>
      <el-table-column :label="t('change.type')" width="130">
        <template #default="{ row }">
          {{ enumLabel('changeType', row.changeType) || row.changeTypeLabel }}
        </template>
      </el-table-column>
      <el-table-column :label="t('change.before')" width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ beforeText(row) }}</template>
      </el-table-column>
      <el-table-column :label="t('change.after')" width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ afterText(row) }}</template>
      </el-table-column>
      <el-table-column prop="changeReason" :label="t('change.reason')" width="160" show-overflow-tooltip />
      <el-table-column prop="effectiveDate" :label="t('change.effective')" width="120" />
      <el-table-column :label="t('change.statusCol')" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.approveStatus === 'APPROVED' ? 'success'
            : (row.approveStatus === 'REJECTED' ? 'danger' : 'warning')">
            {{ row.approveStatusLabel || enumLabel('changeStatus', row.approveStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('change.actions')" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="success" :disabled="row.approveStatus === 'APPROVED'"
                     @click="approve(row)">{{ t('change.approve') }}</el-button>
          <el-button link type="danger" :disabled="row.approveStatus === 'REJECTED'"
                     @click="reject(row)">{{ t('change.reject') }}</el-button>
          <el-button link @click="openChange(row)">{{ t('change.detail') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="changeVisible" :title="t('change.detailTitle')" width="760px">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item :label="t('change.no')">{{ current?.changeNo }}</el-descriptions-item>
        <el-descriptions-item :label="t('change.contract')">{{ current?.contractIdName || current?.contractId }}</el-descriptions-item>
        <el-descriptions-item :label="t('change.type')">{{ enumLabel('changeType', current?.changeType) || current?.changeTypeLabel }}</el-descriptions-item>
        <el-descriptions-item :label="t('change.effective')">{{ current?.effectiveDate }}</el-descriptions-item>
        <el-descriptions-item :label="t('change.statusCol')">{{ current?.approveStatusLabel || current?.approveStatus }}</el-descriptions-item>
        <el-descriptions-item :label="t('change.reason')">{{ current?.changeReason || '—' }}</el-descriptions-item>
      </el-descriptions>
      <el-row :gutter="12" style="margin-top:10px">
        <el-col :span="12">
          <div class="card-title">{{ t('misc2.before') }}</div>
          <div class="kv">
            <div v-for="(v, k) in beforeObj" :key="k"><b>{{ k }}</b>：{{ v }}</div>
            <div v-if="!Object.keys(beforeObj).length" class="muted">—</div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card-title">{{ t('misc2.after') }}</div>
          <div class="kv">
            <div v-for="(v, k) in afterObj" :key="k"><b>{{ k }}</b>：{{ v }}</div>
            <div v-if="!Object.keys(afterObj).length" class="muted">—</div>
          </div>
        </el-col>
      </el-row>
      <template #footer>
        <el-button @click="changeVisible = false">{{ t('change.close') }}</el-button>
      </template>
    </el-dialog>

    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="query.pageSize"
                   :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />

    <el-drawer v-model="show" :title="t('change.drawerTitle')" size="520px">
      <DetailView :row="detail || {}" />
    </el-drawer>
    <el-dialog v-model="createVisible" :title="t('change.createTitle')" width="520px">
      <el-form :model="cf" label-width="120px">
        <el-form-item :label="t('change.contractId')" required>
          <el-input v-model.number="cf.contractId" />
        </el-form-item>
        <el-form-item :label="t('change.type')" required>
          <el-select v-model="cf.changeType" style="width:100%">
            <el-option :label="t('change.rentAdjust')" value="RENT_ADJUST" />
            <el-option :label="t('change.renew')" value="RENEW" />
            <el-option :label="t('change.period')" value="PERIOD" />
            <el-option :label="t('change.lesseeChange')" value="LESSEE" />
            <el-option :label="t('change.other')" value="OTHER" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="cf.changeType === 'RENT_ADJUST' || cf.changeType === 'RENEW'"
                      :label="t('change.newRent')">
          <el-input v-model.number="cf.newMonthlyRent" />
        </el-form-item>
        <el-form-item v-if="cf.changeType === 'PERIOD' || cf.changeType === 'RENEW'"
                      :label="t('change.newEnd')">
          <el-date-picker v-model="cf.newLeaseEnd" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
        <el-form-item :label="t('change.reasonLabel')">
          <el-input v-model="cf.changeReason" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">{{ t('change.cancel') }}</el-button>
        <el-button type="primary" @click="doCreateChange">{{ t('change.create') }}</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import { enumLabel } from '@/constants/enums'
import DetailView from '@/components/DetailView.vue'

const { t, locale } = useI18n()
const isEn = () => locale.value === 'en-US'
const statuses = ['PENDING', 'APPROVED', 'REJECTED', 'CANCELLED']
const loading = ref(false)
const rows = ref([])
const total = ref(0)

const KV_LABEL = { monthlyRent: '月租金', leaseEnd: '止租日', leaseStart: '起租日',
  lesseePersonId: '承租人ID', lesseeName: '承租人', depositAmount: '押金',
  contractNo: '合同号', houseId: '房源', remark: '备注', rentPrice: '租金单价' }
const KV_LABEL_EN = { monthlyRent: 'Monthly Rent', leaseEnd: 'Lease End', leaseStart: 'Lease Start',
  lesseePersonId: 'Lessee ID', lesseeName: 'Lessee', depositAmount: 'Deposit',
  contractNo: 'Contract No.', houseId: 'Housing', remark: 'Remark', rentPrice: 'Rent Price',
  subsidyAmount: 'Subsidy', payCycle: 'Payment Cycle', payDay: 'Billing Day' }

function kvText(raw) {
  if (raw == null || raw === '') return '—'
  let obj = raw
  if (typeof raw === 'string') {
    try { obj = JSON.parse(raw) } catch (e) { return raw }
  }
  if (!obj || typeof obj !== 'object') return String(obj)
  return Object.keys(obj).map((k) => ((isEn() ? KV_LABEL_EN[k] : KV_LABEL[k]) || k) + (isEn() ? ': ' : '：') + obj[k]).join(isEn() ? '; ' : '；')
}
function beforeText(row) { return kvText(row.beforeJson ?? row.before) }
function afterText(row) { return kvText(row.afterJson ?? row.after) }
const changeVisible = ref(false)
const current = ref(null)
const beforeObj = ref({})
const afterObj = ref({})

const FIELD_LABEL = {
  monthlyRent: '月租金', depositAmount: '押金', leaseStart: '开始日', leaseEnd: '结束日',
  lesseePersonId: '承租人', lesseeName: '承租人姓名', payCycle: '付款周期',
  payDay: '账单日', rentPrice: '租金单价', actualPay: '实付', subsidyAmount: '补贴',
  houseId: '房源', remark: '备注'
}
const FIELD_LABEL_EN = {
  monthlyRent: 'Monthly Rent', depositAmount: 'Deposit', leaseStart: 'Lease Start',
  leaseEnd: 'Lease End', lesseePersonId: 'Lessee', lesseeName: 'Lessee Name',
  payCycle: 'Payment Cycle', payDay: 'Billing Day', rentPrice: 'Rent Price',
  actualPay: 'Actual Pay', subsidyAmount: 'Subsidy', houseId: 'Housing', remark: 'Remark'
}

function pretty(raw) {
  if (raw == null || raw === '') return {}
  let obj = raw
  if (typeof raw === 'string') {
    try { obj = JSON.parse(raw) } catch (e) { return { [isEn() ? 'Content' : '内容']: raw } }
  }
  if (Array.isArray(obj)) return { [isEn() ? 'Content' : '内容']: obj.join(isEn() ? ', ' : '、') }
  if (typeof obj !== 'object') return { [isEn() ? 'Content' : '内容']: String(obj) }
  const out = {}
  Object.keys(obj).forEach((k) => { out[(isEn() ? FIELD_LABEL_EN[k] : FIELD_LABEL[k]) || k] = obj[k] })
  return out
}

function openChange(row) {
  current.value = row
  beforeObj.value = pretty(row.beforeJson ?? row.beforeContent ?? row.before)
  afterObj.value = pretty(row.afterJson ?? row.afterContent ?? row.after)
  changeVisible.value = true
}
const show = ref(false)
const detail = ref(null)
const query = reactive({ pageNum: 1, pageSize: 20, changeStatus: '' })

async function load() {
  loading.value = true
  try {
    const d = await req.get('/contract-changes', {
      params: { ...query, status: query.changeStatus || undefined }
    })
    rows.value = d.rows || d || []
    total.value = Number(d.total || rows.value.length || 0)
  } catch (e) { rows.value = []; total.value = 0 } finally { loading.value = false }
}
function reload() { query.pageNum = 1; load() }

async function approve(row) {
  await ElMessageBox.confirm(
    `确认批准变更「${row.changeNo}」？批准后会写回合同并即时生效。`, '批准确认',
    { type: 'warning' })
  await req.post(`/contract-changes/${row.id}/approve`)
  ElMessage.success('已批准'); load()
}

async function reject(row) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因', '驳回变更',
    { inputValue: '' })
  await req.post(`/contract-changes/${row.id}/reject`, { reason: value })
  ElMessage.success('已驳回'); load()
}

const query0 = JSON.parse(JSON.stringify(query))
function resetQuery() {
  Object.assign(query, query0)
  reload()
}

onMounted(load)
const createVisible = ref(false)
const cf = reactive({ contractId: null, changeType: 'RENT_ADJUST',
  newMonthlyRent: null, newLeaseEnd: '', changeReason: '' })

function openCreate() {
  Object.assign(cf, { contractId: null, changeType: 'RENT_ADJUST',
    newMonthlyRent: null, newLeaseEnd: '', changeReason: '' })
  createVisible.value = true
}

/** 从合同发起变更（统一走 /contracts/{id}/changes） */
async function doCreateChange() {
  if (!cf.contractId) { ElMessage.warning('请填写合同ID'); return }
  if (cf.changeType === 'RENT_ADJUST' && !cf.newMonthlyRent) {
    ElMessage.warning('调租请填写新租金'); return
  }
  await req.post(`/contracts/${cf.contractId}/changes`, {
    changeType: cf.changeType,
    changeReason: cf.changeReason,
    newMonthlyRent: cf.newMonthlyRent || null,
    newLeaseEnd: cf.newLeaseEnd || null
  })
  ElMessage.success('变更单已创建，待审批')
  createVisible.value = false
  load()
}
</script>
