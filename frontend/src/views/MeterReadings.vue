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
      <el-button type="primary" plain @click="openBatch" data-testid="meter-batch">
        批量录入/导入
      </el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
              title="用量 = 本次读数 − 上次读数；金额 = 用量 × 计费项目单价（单价在「计费项目」中维护）" />

    <el-table empty-text="暂无抄表记录，可人工录入或从 IoT 拉取" :data="rows" v-loading="loading" border size="small">
      <el-table-column prop="readDate" label="抄表日期" width="120" />
      <el-table-column prop="houseId" label="房源" min-width="180">
        <template #default="{ row }">{{ row.houseIdName || houseLabel(row.houseId) }}</template>
      </el-table-column>
      <el-table-column prop="feeItemId" label="计量项目" width="150">
        <template #default="{ row }">{{ row.feeItemIdName || itemLabel(row.feeItemId) }}</template>
      </el-table-column>
      <el-table-column prop="reading" label="本次读数" width="110" />
      <el-table-column prop="multiplier" label="倍率" width="80" />
      <el-table-column prop="unit" label="单位" width="70" />
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

    <!-- 单条录入：按房源 + 计量项目带出设备，多设备逐台录入 -->
    <el-dialog v-model="recordVisible" title="录入抄表读数" width="640px">
      <el-form :model="rf" label-width="100px">
        <el-form-item label="房源" required>
          <HouseSelect v-model="rf.houseId" width="100%" testid="meter-house" />
        </el-form-item>
        <el-form-item label="计量项目" required>
          <el-select v-model="rf.feeItemId" style="width:100%" placeholder="水费/电费等"
                     @change="loadDevices">
            <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                       :label="m.itemName + '（' + m.unitPrice + ' 元/' + (m.unit || '度') + '）'" />
          </el-select>
        </el-form-item>
        <el-form-item label="抄表日期">
          <el-date-picker v-model="rf.readDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert v-if="devices.length" type="info" :closable="false" show-icon
                :title="'该房源在此计量项目下共 ' + devices.length + ' 台设备，逐台录入读数'" />
      <el-table v-if="devices.length" :data="deviceRows" size="small" border style="margin-top:8px">
        <el-table-column prop="deviceType" label="设备类型" width="110" />
        <el-table-column prop="deviceId" label="设备编号" width="170" />
        <el-table-column prop="deviceName" label="设备名称" min-width="140" />
        <el-table-column label="本次读数" width="160">
          <template #default="{ row }"><el-input v-model="row.reading" /></template>
        </el-table-column>
      </el-table>
      <el-form v-else label-width="100px" style="margin-top:8px">
        <el-form-item label="计量设备编号">
          <DeviceSelect v-model="rf.deviceId" width="100%" testid="device-select" />
        </el-form-item>
        <el-form-item label="本次读数" required>
          <el-input v-model="rf.reading" />
        </el-form-item>
        <el-alert type="warning" :closable="false" style="margin-top:4px"
                  title="该房源在此计量项目下未绑定设备：可手工选择设备或留空按人工录入" />
      </el-form>
      <template #footer>
        <el-button @click="recordVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRecord">录入</el-button>
      </template>
    </el-dialog>

    <!-- 导出 CSV 模板 -->
    <el-dialog v-model="exportVisible" title="导出抄表 CSV" width="520px">
      <el-form label-width="90px">
        <el-form-item label="组织">
          <el-select v-model="ex.orgId" filterable clearable style="width:100%"
                     placeholder="选择组织" @change="loadExportSpaces">
            <el-option v-for="o in exOrgs" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item label="空间">
          <el-select v-model="ex.spaceId" filterable clearable style="width:100%"
                     placeholder="选择空间（含下级），可空表示整个组织">
            <el-option v-for="s in exSpaces" :key="s.id" :label="s.label" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="计量项目" required>
          <el-select v-model="ex.feeItemId" style="width:100%">
            <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                       :label="m.itemName" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                title="导出的表格含组织/空间/房源/计费项目/设备信息，读数留空；填好后直接导入即可。" />
      <template #footer>
        <el-button @click="exportVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doExport">导出</el-button>
      </template>
    </el-dialog>

    <!-- 批量录入 / CSV 导入 -->
    <el-dialog v-model="batchVisible" title="批量录入 / 导入抄表" width="1180px">
      <div class="toolbar" style="margin-bottom:8px">
        <el-button size="small" type="primary" plain @click="openExport">导出 CSV 模板</el-button>
        <el-button size="small" @click="addBatchRow">添加一行</el-button>
        <el-upload :auto-upload="false" :limit="1" accept=".csv" :show-file-list="false"
                   :on-change="onCsv">
          <el-button size="small">导入 CSV</el-button>
        </el-upload>
        <span class="muted" style="font-size:12px">
          导出 → 填读数 → 原样导入（列：组织,空间,房源编号,房源名称,计费项目,设备编号,设备名称,设备类型,读数,抄表日期）
        </span>
      </div>
      <el-table :data="batchRows" size="small" border max-height="380">
        <el-table-column label="房源" width="200">
          <template #default="{ row }">
            <HouseSelect :model-value="row.houseId" width="100%"
                         @update:model-value="(v) => onRowHouse(row, v)" />
          </template>
        </el-table-column>
        <el-table-column label="计量项目" width="150">
          <template #default="{ row }">
            <el-select v-model="row.feeItemId" size="small" style="width:100%"
                       @change="fillRowDevice(row)">
              <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                         :label="m.itemName" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="设备编号" width="160">
          <template #default="{ row }">
            <el-select v-if="row.devices && row.devices.length > 1" v-model="row.deviceId"
                       size="small" style="width:100%" @change="pickDevice(row)">
              <el-option v-for="d in row.devices" :key="d.device_id"
                         :label="d.device_id" :value="d.device_id" />
            </el-select>
            <el-input v-else v-model="row.deviceId" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="deviceName" label="设备名称" width="170" />
        <el-table-column prop="deviceType" label="设备类型" width="120" />
        <el-table-column label="读数" width="100">
          <template #default="{ row }"><el-input v-model="row.reading" size="small" /></template>
        </el-table-column>
        <el-table-column label="抄表日期" width="135">
          <template #default="{ row }">
            <el-date-picker v-model="row.readDate" type="date" value-format="YYYY-MM-DD"
                            size="small" style="width:100%" />
          </template>
        </el-table-column>
        <el-table-column label="" width="60">
          <template #default="{ $index }">
            <el-button link type="danger" @click="batchRows.splice($index, 1)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-alert v-if="batchResult" :type="batchResult.failed ? 'warning' : 'success'"
                :closable="false" style="margin-top:8px"
                :title="'共 ' + batchResult.total + ' 行，成功 ' + batchResult.created
                  + '，失败 ' + batchResult.failed" />
      <template #footer>
        <el-button @click="batchVisible = false">关闭</el-button>
        <el-button type="primary" :loading="saving" @click="doBatch">提交</el-button>
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
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import req from '@/api/request'
import DeviceSelect from '@/components/DeviceSelect.vue'
import HouseSelect from '@/components/HouseSelect.vue'

const rows = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const houses = ref([])
const meterItems = ref([])
const recordVisible = ref(false)
const query = reactive({ pageNum: 1, pageSize: 20, houseId: '', feeItemId: '' })
const rf = reactive({ houseId: '', feeItemId: '', reading: '', readDate: '', deviceId: '' })
const devices = ref([])
const deviceRows = ref([])
const batchVisible = ref(false)
const batchRows = ref([])
const batchResult = ref(null)
const exportVisible = ref(false)
const ex = reactive({ orgId: '', spaceId: '', feeItemId: '' })
const exOrgs = ref([])
const exSpaces = ref([])

async function loadExportOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    exOrgs.value = (d && d.rows) || []
  } catch (e) { exOrgs.value = [] }
}

function flattenSpaces(list, out) {
  (list || []).forEach((n) => {
    if (['ROOM', 'BED'].includes(n.spaceType)) {
      out.push({ id: n.id, label: n.fullName || n.spaceName })
    }
    if (n.children && n.children.length) flattenSpaces(n.children, out)
  })
}

async function loadExportSpaces() {
  ex.spaceId = ''
  exSpaces.value = []
  if (!ex.orgId) return
  try {
    const tree = await req.get('/spaces/tree', { params: { orgId: ex.orgId } })
    const out = []
    flattenSpaces(tree || [], out)
    exSpaces.value = out
  } catch (e) { exSpaces.value = [] }
}

function openExport() {
  ex.feeItemId = query.feeItemId || ''
  ex.orgId = ''
  ex.spaceId = ''
  exSpaces.value = []
  exportVisible.value = true
  loadExportOrgs()
}

function csvCell(v) {
  const t = v == null ? '' : String(v)
  return /[",\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t
}

async function doExport() {
  if (!ex.feeItemId) { ElMessage.warning('请选择计量项目'); return }
  saving.value = true
  try {
    const list = await req.get('/fin/meter-readings/export-template', {
      params: { orgId: ex.orgId || undefined, spaceId: ex.spaceId || undefined,
        feeItemId: ex.feeItemId }
    })
    if (!list || !list.length) { ElMessage.warning('所选范围没有房源'); return }
    const heads = ['组织', '空间', '房源编号', '房源名称', '计费项目',
      '设备编号', '设备名称', '设备类型', '读数', '抄表日期']
    const lines = [heads.join(',')].concat((list || []).map((r) => [
      r.orgName, r.spaceName, r.houseCode, r.houseName, r.feeItemName,
      r.deviceId, r.deviceName, r.deviceType, '', r.readDate].map(csvCell).join(',')))
    const blob = new Blob(['\ufeff' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = '抄表导入_' + new Date().toISOString().slice(0, 10) + '.csv'
    a.click()
    URL.revokeObjectURL(a.href)
    ElMessage.success('已导出 ' + list.length + ' 行')
    exportVisible.value = false
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导出失败')
  } finally { saving.value = false }
}

/** 批量行：选房源+项目后自动带出设备 */
async function fillRowDevice(row) {
  row.devices = []
  row.deviceId = ''
  row.deviceName = ''
  row.deviceType = ''
  if (!row.houseId || !row.feeItemId) return
  try {
    const list = await req.get('/fin/meter-readings/devices',
      { params: { houseId: row.houseId, feeItemId: row.feeItemId } })
    row.devices = list || []
    if (row.devices.length === 1) {
      row.deviceId = row.devices[0].device_id
      row.deviceName = row.devices[0].device_name
      row.deviceType = row.devices[0].device_type
    } else if (row.devices.length > 1) {
      row.deviceId = row.devices[0].device_id
      row.deviceName = row.devices[0].device_name
      row.deviceType = row.devices[0].device_type
    }
  } catch (e) { /* 忽略 */ }
}

function pickDevice(row) {
  const d = (row.devices || []).find((x) => x.device_id === row.deviceId)
  row.deviceName = d ? d.device_name : ''
  row.deviceType = d ? d.device_type : ''
}

watch(() => [rf.houseId, rf.feeItemId], () => loadDevices())

function onRowHouse(row, v) {
  row.houseId = v
  fillRowDevice(row)
}

async function loadDevices() {
  devices.value = []
  deviceRows.value = []
  if (!rf.houseId || !rf.feeItemId) return
  try {
    const list = await req.get('/fin/meter-readings/devices',
      { params: { houseId: rf.houseId, feeItemId: rf.feeItemId } })
    devices.value = list || []
    deviceRows.value = (list || []).map((d) => ({ ...d, reading: '' }))
  } catch (e) { devices.value = [] }
}

function openBatch() {
  batchRows.value = []
  batchResult.value = null
  addBatchRow()
  batchVisible.value = true
}

function addBatchRow() {
  batchRows.value.push({ houseId: query.houseId || '', feeItemId: query.feeItemId || '',
    deviceId: '', reading: '', readDate: new Date().toISOString().slice(0, 10) })
}

function downloadTemplate() {
  const csv = '\ufeff房源编号,计量项目,设备编号,读数,抄表日期\n'
    + 'H8063501,电费,DEMO-ELEC-00001,1200.5,2026-10-28\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '抄表导入模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

function parseCsv(text) {
  const rows = []
  text.replace(/^\ufeff/, '').split(/\r?\n/).forEach((line) => {
    if (!line.trim()) return
    rows.push(line.split(',').map((x) => x.trim().replace(/^"|"$/g, '')))
  })
  return rows
}

function onCsv(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const all = parseCsv(String(e.target.result || ''))
    if (!all.length) { ElMessage.warning('文件为空'); return }
    const head = all[0]
    const idx = (name) => head.findIndex((h) => h.includes(name))
    const hasHeader = idx('房源编号') >= 0
    const body = hasHeader ? all.slice(1) : all
    const at = (c, name, fallback) => {
      const i = hasHeader ? idx(name) : fallback
      return i >= 0 ? (c[i] || '') : ''
    }
    batchRows.value = body.map((c) => {
      const houseCode = at(c, '房源编号', 0)
      const itemName = at(c, '计费项目', 1)
      const house = houses.value.find((h) => String(h.houseCode) === houseCode
        || String(h.houseName) === houseCode)
      const item = meterItems.value.find((m) => m.itemName === itemName
        || String(m.itemCode) === itemName)
      return { houseId: house ? house.id : '', feeItemId: item ? item.id : '',
        deviceId: at(c, '设备编号', 2), deviceName: at(c, '设备名称', 3),
        deviceType: at(c, '设备类型', 4), devices: [],
        reading: at(c, '读数', 5), readDate: at(c, '抄表日期', 6) }
    })
    ElMessage.success('已解析 ' + batchRows.value.length + ' 行，请核对后提交')
  }
  reader.readAsText(file.raw, 'utf-8')
}

async function doBatch() {
  const cmds = batchRows.value.filter((r) => r.houseId && r.feeItemId && r.reading !== '')
    .map((r) => ({ houseId: r.houseId, feeItemId: r.feeItemId,
      deviceId: r.deviceId || undefined, reading: Number(r.reading),
      readDate: r.readDate || undefined }))
  if (!cmds.length) { ElMessage.warning('没有可提交的行'); return }
  saving.value = true
  try {
    batchResult.value = await req.post('/fin/meter-readings/batch', cmds)
    ElMessage.success('提交完成：成功 ' + batchResult.value.created
      + '，失败 ' + batchResult.value.failed)
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '批量提交失败')
  } finally { saving.value = false }
}

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
  devices.value = []
  deviceRows.value = []
  recordVisible.value = true
  loadDevices()
}

async function doRecord() {
  if (!rf.houseId || !rf.feeItemId) {
    ElMessage.warning('请选择房源与计量项目'); return
  }
  let cmds = []
  if (deviceRows.value.length) {
    cmds = deviceRows.value.filter((d) => d.reading !== '' && d.reading != null)
      .map((d) => ({ houseId: rf.houseId, feeItemId: rf.feeItemId,
        deviceId: d.deviceId, reading: Number(d.reading),
        readDate: rf.readDate || undefined }))
    if (!cmds.length) { ElMessage.warning('请至少填写一台设备的读数'); return }
  } else {
    if (rf.reading === '') { ElMessage.warning('请填写本次读数'); return }
    cmds = [{ houseId: rf.houseId, feeItemId: rf.feeItemId,
      deviceId: rf.deviceId || undefined, reading: Number(rf.reading),
      readDate: rf.readDate || undefined }]
  }
  saving.value = true
  try {
    const r = await req.post('/fin/meter-readings/batch', cmds)
    ElMessage.success('录入完成：成功 ' + r.created + '，失败 ' + r.failed)
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
