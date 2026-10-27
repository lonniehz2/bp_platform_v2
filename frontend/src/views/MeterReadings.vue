<template>
  <div>
    <div class="toolbar">
      <el-select v-model="query.houseId" placeholder="房源" clearable filterable
                 style="width:240px" @change="load">
        <el-option v-for="h in houses" :key="h.id" :value="h.id"
                   :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'" />
      </el-select>
      <el-select v-model="query.feeItemId" placeholder="计量项目（水/电/燃气）" clearable
                 style="width:220px" @change="load">
        <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                   :label="m.itemName + '（' + m.unitPrice + ' 元/' + (m.unit || '度') + '）'" />
      </el-select>
      <el-button type="primary" @click="load">查询</el-button>
      <el-button @click="resetQuery">清空</el-button>
      <el-button type="warning" plain :loading="pulling" @click="pullFromIot">
        从 IoT 拉取
      </el-button>
      <el-button type="success" plain @click="openRecord" data-testid="meter-new">
        录入读数
      </el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
              title="用量 = 本次读数 − 上次读数；金额 = 用量 × 计费项目单价（单价在「计费项目」中维护）" />

    <el-table :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="readDate" label="抄表日期" width="120" />
      <el-table-column prop="houseId" label="房源" min-width="180">
        <template #default="{ row }">{{ row.houseIdName || houseLabel(row.houseId) }}</template>
      </el-table-column>
      <el-table-column prop="feeItemId" label="计量项目" width="150">
        <template #default="{ row }">{{ row.feeItemIdName || itemLabel(row.feeItemId) }}</template>
      </el-table-column>
      <el-table-column prop="reading" label="本次读数" width="110" />
      <el-table-column prop="lastReading" label="上次读数" width="110">
        <template #default="{ row }">{{ lastOf(row) }}</template>
      </el-table-column>
      <el-table-column prop="usageAmount" label="用量" width="100">
        <template #default="{ row }">{{ row.usageAmount != null ? row.usageAmount : '—' }}</template>
      </el-table-column>
      <el-table-column prop="amount" label="金额" width="110">
        <template #default="{ row }">{{ row.amount != null ? row.amount : '—' }}</template>
      </el-table-column>
      <el-table-column prop="deviceId" label="计量设备" width="160">
        <template #default="{ row }">{{ row.deviceId || '人工录入' }}</template>
      </el-table-column>
      <el-table-column prop="billId" label="出账状态" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.billId ? 'success' : 'info'">
            {{ row.billId ? '已出账' : '未出账' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="110" fixed="right">
        <template #default="{ row }">
          <el-button v-if="!row.billId" link type="primary"
                     @click="doBill(row)" data-testid="meter-bill">出账</el-button>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top:12px" layout="total, prev, pager, next"
                   :total="total" :page-size="query.pageSize" :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }" />

    <!-- 录入读数 -->
    <el-dialog v-model="recordVisible" title="录入抄表读数" width="560px">
      <el-form :model="rf" label-width="100px">
        <el-form-item label="房源" required>
          <el-select v-model="rf.houseId" filterable style="width:100%"
                     placeholder="选择房源">
            <el-option v-for="h in houses" :key="h.id" :value="h.id"
                       :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'" />
          </el-select>
        </el-form-item>
        <el-form-item label="计量项目" required>
          <el-select v-model="rf.feeItemId" style="width:100%" placeholder="水费/电费等">
            <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                       :label="m.itemName + '（' + m.unitPrice + ' 元/' + (m.unit || '度') + '）'" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="本次读数" required>
            <el-input v-model="rf.reading" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="抄表日期">
            <el-date-picker v-model="rf.readDate" type="date" value-format="YYYY-MM-DD"
                            style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="计量设备编号">
          <DeviceSelect v-model="rf.deviceId" width="100%" testid="device-select" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="recordVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRecord">录入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 抄表管理：水电燃气等计量设备的读数录入、用量计算与出账。
 *
 * 单价来自「计费项目」（calcMode=METER），本页只负责读数与出账。
 */
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import DeviceSelect from '@/components/DeviceSelect.vue'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const houses = ref([])
const meterItems = ref([])
const recordVisible = ref(false)
const query = reactive({ pageNum: 1, pageSize: 20, houseId: '', feeItemId: '' })
const rf = reactive({ houseId: '', feeItemId: '', reading: '', readDate: '', deviceId: '' })

function lastOf(row) {
  if (row.lastReading != null) return row.lastReading
  if (row.reading != null && row.usageAmount != null) {
    const v = Number(row.reading) - Number(row.usageAmount)
    return Number.isFinite(v) ? v.toFixed(2) : '—'
  }
  return '—'
}

function houseLabel(id) {
  const h = houses.value.find((x) => String(x.id) === String(id))
  return h ? (h.houseName || h.houseCode) : id
}

function itemLabel(id) {
  const m = meterItems.value.find((x) => String(x.id) === String(id))
  return m ? m.itemName : id
}

async function loadBase() {
  try {
    const hs = await req.get('/houses', { params: { pageNum: 1, pageSize: 300 } })
    houses.value = (hs && hs.rows) || []
    const items = await req.get('/fin/fee-items', { params: { pageNum: 1, pageSize: 100 } })
    meterItems.value = ((items && items.rows) || []).filter((x) => x.calcMode === 'METER')
  } catch (e) {
    ElMessage.error('加载房源/计量项目失败')
  }
}

async function load() {
  loading.value = true
  try {
    const params = { pageNum: query.pageNum, pageSize: query.pageSize }
    if (query.houseId) params.houseId = query.houseId
    if (query.feeItemId) params.feeItemId = query.feeItemId
    const r = await req.get('/fin/meter-readings', { params })
    rows.value = (r && r.rows) || []
    total.value = (r && r.total) || 0
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '加载抄表记录失败')
  } finally { loading.value = false }
}

function resetQuery() {
  Object.assign(query, { pageNum: 1, houseId: '', feeItemId: '' })
  load()
}

const pulling = ref(false)

async function pullFromIot() {
  pulling.value = true
  try {
    const r = await req.post('/iot/meter/pull')
    ElMessage.success('拉取完成：表 ' + r.meters + ' 台，读数 ' + r.fetched
      + ' 条，入库 ' + r.ingested + ' 条')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '拉取失败')
  } finally { pulling.value = false }
}

function openRecord() {
  Object.assign(rf, { houseId: query.houseId || '', feeItemId: query.feeItemId || '',
    reading: '', readDate: new Date().toISOString().slice(0, 10), deviceId: '' })
  recordVisible.value = true
}

async function doRecord() {
  if (!rf.houseId || !rf.feeItemId || rf.reading === '') {
    ElMessage.warning('请填写房源、计量项目与本次读数'); return
  }
  saving.value = true
  try {
    await req.post('/fin/meter-readings', {
      houseId: rf.houseId, feeItemId: rf.feeItemId,
      reading: Number(rf.reading), readDate: rf.readDate || undefined,
      deviceId: rf.deviceId || undefined
    })
    ElMessage.success('读数已录入')
    recordVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '录入失败')
  } finally { saving.value = false }
}

async function doBill(row) {
  try {
    await req.post(`/fin/meter-readings/${row.id}/bill`)
    ElMessage.success('已出账')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '出账失败')
  }
}

onMounted(async () => {
  await loadBase()
  load()
})
</script>
