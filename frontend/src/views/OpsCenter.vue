<template>
  <div class="page-card">
    <div class="toolbar">
      <h3 style="margin:0">{{ t('ops.title') }}</h3>
      <el-tag size="small" type="info">人员/房源状态 · 工单全流程</el-tag>
      <div class="spacer" />
      <el-button @click="loadAll">{{ t('ops.refresh') }}</el-button>
    </div>

    <el-alert type="warning" :closable="false" show-icon
              title="状态变更会同步影响门禁授权与业务校验，请谨慎操作"
              style="margin-bottom:12px" />

    <el-tabs v-model="tab">
      <!-- 人员 -->
      <el-tab-pane :label="t('ops.personTab')" name="person">
        <div class="toolbar" style="margin-bottom:10px">
          <PersonPicker v-model="pid" width="200px" testid="picker" />
          <el-select v-model="pStatus" style="width:160px">
            <el-option :label="t('ops.normal')" value="NORMAL" />
            <el-option :label="t('ops.frozen')" value="FROZEN" />
            <el-option :label="t('ops.cancelled')" value="CANCELLED" />
          </el-select>
          <el-button type="primary" :loading="saving" @click="setPersonStatus">
            变更人员状态
          </el-button>
        </div>
                <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="filters.person" :placeholder="t('ops.personHint')" clearable style="width:200px"
                    data-testid="oc-person" @keyup.enter="loadAll" />
          <el-button type="primary" @click="loadAll">{{ t('ops.search') }}</el-button>
          <el-button @click="resetFilter('person')">{{ t('ops.reset') }}</el-button>
        </div>
<el-table :data="persons" border size="small" max-height="380">
          <el-table-column prop="id" :label="t('ops.id')" width="180" />
          <el-table-column prop="personName" :label="t('ops.name')" width="120" />
          <el-table-column :label="t('ops.phone')" width="140">
          <template #default="{ row }">{{ row.phone || '—' }}</template>
        </el-table-column>
          <el-table-column prop="personStatus" :label="t('ops.status')" width="120">
            <template #default="{ row }">{{ row.personStatusLabel || enumLabel('personStatus', row.personStatus) }}</template>
          </el-table-column>
          <el-table-column :label="t('ops.actions')" width="120">
            <template #default="{ row }">
              <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">{{ t('ops.detail') }}</el-button>
              <el-button link type="primary" @click="pid = row.id; pStatus =
                row.personStatus || 'NORMAL'">{{ t('ops.select') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 房源 -->
      <el-tab-pane :label="t('ops.houseTab')" name="house">
        <div class="toolbar" style="margin-bottom:10px">
          <HouseSelect v-model="hid" width="200px" testid="house-select" />
          <el-select v-model="hStatus" style="width:170px">
            <el-option :label="t('ops.vacant')" value="VACANT" />
            <el-option :label="t('ops.occupied')" value="OCCUPIED" />
            <el-option :label="t('ops.locked')" value="LOCKED" />
            <el-option :label="t('ops.repair')" value="REPAIR" />
            <el-option :label="t('ops.offline')" value="OFFLINE" />
          </el-select>
          <el-button type="primary" :loading="saving" @click="setHouseStatus">
            变更房源状态
          </el-button>
        </div>
                <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="filters.house" :placeholder="t('ops.houseName')" clearable style="width:200px"
                    data-testid="oc-house" @keyup.enter="loadAll" />
          <el-button type="primary" @click="loadAll">查询</el-button>
          <el-button @click="resetFilter('house')">{{ t('ops.reset') }}</el-button>
        </div>
<el-table :data="houses" border size="small" max-height="380">
          <el-table-column prop="houseCode" :label="t('ops.houseCode')" width="160" />
          <el-table-column prop="houseName" :label="t('ops.houseName')" min-width="140" />
          <el-table-column prop="houseStatus" :label="t('ops.status')" width="120">
            <template #default="{ row }">{{ row.houseStatusLabel || enumLabel('houseStatus', row.houseStatus) }}</template>
          </el-table-column>
          <el-table-column prop="area" :label="t('ops.area')" width="90" />
          <el-table-column :label="t('ops.actions')" width="110">
            <template #default="{ row }">
              <el-button link type="primary" @click="hid = row.id; hStatus =
                row.houseStatus || 'VACANT'">{{ t('ops.select') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 工单 -->
      <el-tab-pane :label="t('ops.orderTab')" name="order">
                <div class="toolbar" style="margin-bottom:8px">
          <el-input v-model="filters.order" :placeholder="t('ops.orderNo')" clearable style="width:200px"
                    data-testid="oc-order" @keyup.enter="loadAll" />
          <el-button type="primary" @click="loadAll">查询</el-button>
          <el-button @click="resetFilter('order')">{{ t('ops.reset') }}</el-button>
        </div>
<el-table :data="orders" border size="small" max-height="440">
          <el-table-column prop="workorderNo" :label="t('ops.orderNo')" width="170" />
          <el-table-column prop="orderType" :label="t('ops.type')" width="120">
            <template #default="{ row }">{{ row.workOrderTypeLabel || enumLabel('orderType', row.orderType) }}</template>
          </el-table-column>
          <el-table-column prop="orderStatus" :label="t('ops.status')" width="120">
            <template #default="{ row }">{{ row.workOrderStatusLabel || enumLabel('orderStatus', row.orderStatus) }}</template>
          </el-table-column>
          <el-table-column prop="orderTitle" :label="t('ops.titleCol')" min-width="150" />
          <el-table-column :label="t('ops.flowActions')" width="380" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="assign(row)">{{ t('ops.assign') }}</el-button>
              <el-button link @click="orderAct(row, 'accept', t('ops.accept'))">{{ t('ops.accept') }}</el-button>
              <el-button link @click="orderAct(row, 'start', t('ops.start'))">{{ t('ops.start') }}</el-button>
              <el-button link @click="orderAct(row, 'finish', t('ops.finish'))">{{ t('ops.finish') }}</el-button>
              <el-button link type="success" @click="orderAct(row, 'close', t('ops.close'))">
                {{ t('ops.close') }}</el-button>
              <el-button link type="danger" @click="orderAct(row, 'cancel', t('ops.cancel'))">
                {{ t('ops.cancel') }}</el-button>
              <el-button link type="warning" @click="orderAct(row, 'reject', t('ops.reject'))">
                {{ t('ops.reject') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>

    <!-- 通用详情 -->
    <el-dialog v-model="dvVisible" :title="t('ops.detail')" width="820px" top="6vh">
      <DetailView :row="dvRow" />
    </el-dialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
/** 通用详情弹窗（复用 DetailView） */
const { t } = useI18n()
const dvVisible = ref(false)
const dvRow = ref({})
function openDetail(row) {
  dvRow.value = row
  dvVisible.value = true
}

import { enumLabel } from '@/constants/enums'
import { ref, reactive, onMounted, watch } from 'vue'
import DetailView from '@/components/DetailView.vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import req from '@/api/request'
import PersonPicker from '@/components/PersonPicker.vue'
import HouseSelect from '@/components/HouseSelect.vue'

const TABS = ['person', 'house', 'order']
const route = useRoute()
const router = useRouter()
const tab = ref(TABS.includes(route.params.tab) ? route.params.tab : 'person')
const filters = reactive({ person: '', house: '', order: '' })
function resetFilter(k) {
  filters[k] = ''
  loadAll()
}
watch(() => route.params.tab, (v) => {
  const t = TABS.includes(v) ? v : 'person'
  if (t !== tab.value) tab.value = t
})
watch(tab, (v) => {
  if (route.params.tab !== v) router.replace('/ops-center/' + v)
})
const saving = ref(false)
const pid = ref(null)
const hid = ref(null)
const pStatus = ref('NORMAL')
const hStatus = ref('VACANT')
const persons = ref([])
const houses = ref([])
const orders = ref([])

async function loadAll() {
  try {
    const p = await req.get('/persons', { params: { pageNum: 1, pageSize: 20, keyword: filters.person || undefined } })
    persons.value = p.rows || []
  } catch (e) { persons.value = [] }
  try {
    const h = await req.get('/houses', { params: { pageNum: 1, pageSize: 20, keyword: filters.house || undefined } })
    houses.value = h.rows || []
  } catch (e) { houses.value = [] }
  try {
    const o = await req.get('/workorders', { params: { pageNum: 1, pageSize: 20, keyword: filters.order || undefined } })
    orders.value = o.rows || []
  } catch (e) { orders.value = [] }
}

async function setPersonStatus() {
  if (!pid.value) { ElMessage.warning('请选择或填写人员ID'); return }
  saving.value = true
  try {
    await req.post(`/persons/${pid.value}/status`, { status: pStatus.value })
    ElMessage.success('人员状态已更新'); loadAll()
  } finally { saving.value = false }
}

async function setHouseStatus() {
  if (!hid.value) { ElMessage.warning('请选择或填写房源ID'); return }
  saving.value = true
  try {
    await req.post(`/houses/${hid.value}/status`, { status: hStatus.value })
    ElMessage.success('房源状态已更新'); loadAll()
  } finally { saving.value = false }
}

// AssignCmd{assignUserId, assignUserName, assignUserPhone, content}
async function assign(row) {
  const { value } = await ElMessageBox.prompt('请输入处理人工号（用户ID）', '派单',
    { inputValue: '1' })
  await req.post(`/workorders/${row.id}/assign`, {
    assignUserId: String(value).trim(), assignUserName: '维修员', assignUserPhone: '',
    content: '派单处理'
  })
  ElMessage.success('已派单'); loadAll()
}

// ActionCmd{operatorId, operatorName, content, handleResult}
async function orderAct(row, path, label) {
  const { value } = await ElMessageBox.prompt('处理说明（可空）', label,
    { inputValue: '' })
  await req.post(`/workorders/${row.id}/${path}`, {
    operatorId: 1, operatorName: '管理员', content: value || label,
    handleResult: label
  })
  ElMessage.success(label + '成功'); loadAll()
}

onMounted(loadAll)
</script>
