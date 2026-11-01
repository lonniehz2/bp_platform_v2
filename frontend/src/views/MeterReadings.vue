<template>
  <div>
    <div class="toolbar">
      <el-select v-model="query.houseId" :placeholder="t('meter.house')" clearable filterable
                 style="width:240px" @change="load">
        <el-option v-for="h in houses" :key="h.id" :value="h.id"
                   :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'" />
      </el-select>
      <el-select v-model="query.feeItemId" :placeholder="t('meter.feeItemHint')" clearable
                 style="width:220px" @change="load">
        <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                   :label="m.itemName + ' (' + m.unitPrice + ' CNY/' + (m.unit || t('meter.unitDefault')) + ')'" />
      </el-select>
      <el-select v-model="query.orgId" :placeholder="t('meter.org')" clearable filterable
                 style="width:200px" @change="load">
        <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName"
                   :value="String(o.id)" />
      </el-select>
      <el-select v-model="query.billed" :placeholder="t('meter.billed')" clearable
                 style="width:140px" @change="load">
        <el-option :label="t('meter.unbilled')" :value="false" />
        <el-option :label="t('meter.billedYes')" :value="true" />
      </el-select>
      <el-button type="primary" @click="load">{{ t('meter.search') }}</el-button>
      <el-button @click="resetQuery">{{ t('meter.reset') }}</el-button>
      <el-button type="warning" plain :loading="pulling" @click="pullFromIot">{{ t('meter.pull') }}</el-button>
      <el-button type="success" plain @click="openRecord" data-testid="meter-new">{{ t('meter.new') }}</el-button>
      <el-button type="primary" plain @click="openBatch" data-testid="meter-batch">{{ t('meter.batch') }}</el-button>
      <el-button type="warning" plain @click="batchBill">{{ t('meter.batchBill') }}</el-button>
    </div>

    <el-alert type="info" :closable="false" show-icon style="margin-bottom:12px"
              :title="t('meter.tip')" />

    <el-table :empty-text="t('meter.empty')" :data="rows"
              @selection-change="(v) => (meterSelected = v)"
              v-loading="loading" border size="small">
      <el-table-column type="selection" width="42" />
      <el-table-column prop="readDate" :label="t('meter.date')" width="120" />
      <el-table-column prop="houseId" :label="t('meter.house')" min-width="180">
        <template #default="{ row }">{{ row.houseIdName || houseLabel(row.houseId) }}</template>
      </el-table-column>
      <el-table-column prop="feeItemId" :label="t('meter.feeItem')" width="150">
        <template #default="{ row }">{{ row.feeItemIdName || itemLabel(row.feeItemId) }}</template>
      </el-table-column>
      <el-table-column prop="reading" :label="t('meter.reading')" width="110" />
      <el-table-column prop="multiplier" :label="t('meter.multiplier')" width="80" />
      <el-table-column prop="unit" :label="t('meter.unit')" width="70" />
      <el-table-column prop="lastReading" :label="t('meter.last')" width="110">
        <template #default="{ row }">{{ lastOf(row) }}</template>
      </el-table-column>
      <el-table-column prop="usageAmount" :label="t('meter.usage')" width="100">
        <template #default="{ row }">{{ row.usageAmount != null ? row.usageAmount : '—' }}</template>
      </el-table-column>
      <el-table-column prop="amount" :label="t('meter.amount')" width="110">
        <template #default="{ row }">{{ row.amount != null ? row.amount : '—' }}</template>
      </el-table-column>
      <el-table-column prop="deviceId" :label="t('meter.device')" width="160">
        <template #default="{ row }">{{ row.deviceId || t('meter.manualEntry') }}</template>
      </el-table-column>
      <el-table-column prop="billId" :label="t('meter.billStatus')" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="row.billId ? 'success' : 'info'">
            {{ row.billId ? t('meter.billedYes') : t('meter.unbilled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('meter.actions')" width="110" fixed="right">
        <template #default="{ row }">
          <el-button v-if="!row.billId" link type="primary"
                     @click="doBill(row)" data-testid="meter-bill">{{ t('meter.bill') }}</el-button>
          <span v-else class="muted">—</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="meter-pager" data-testid="meter-pager">
    <el-pagination style="margin-top:12px" layout="total, sizes, prev, pager, next"
                   :total="+total || 0" :page-size="query.pageSize" :current-page="query.pageNum"
                   @current-change="(p) => { query.pageNum = p; load() }"  :page-sizes="[10, 20, 50, 100]" @size-change="(s) => { query.pageSize = s; query.pageNum = 1; load() }" />
    </div>

    <!-- 单条录入：按房源 + 计量项目带出设备，多设备逐台录入 -->
    <el-dialog v-model="recordVisible" :title="t('meter.recordTitle')" width="640px">
      <el-form :model="rf" label-width="100px">
        <el-form-item :label="t('meter.house')" required>
          <HouseSelect v-model="rf.houseId" width="100%" testid="meter-house" />
        </el-form-item>
        <el-form-item :label="t('meter.feeItem')" required>
          <el-select v-model="rf.feeItemId" style="width:100%" :placeholder="t('meter.feeItemHint')"
                     @change="loadDevices">
            <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                       :label="m.itemName + '（' + m.unitPrice + ' 元/' + (m.unit || '度') + '）'" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('meter.date')">
          <el-date-picker v-model="rf.readDate" type="date" value-format="YYYY-MM-DD"
                          style="width:100%" />
        </el-form-item>
      </el-form>
      <el-alert v-if="devices.length" type="info" :closable="false" show-icon
                :title="t('meter.recordHint', { n: devices.length })" />
      <el-table v-if="devices.length" :data="deviceRows" size="small" border style="margin-top:8px">
        <el-table-column prop="deviceType" :label="t('meter.deviceType')" width="110" />
        <el-table-column prop="deviceId" :label="t('meter.deviceId')" width="170" />
        <el-table-column prop="deviceName" :label="t('meter.deviceName')" min-width="140" />
        <el-table-column :label="t('meter.reading')" width="160">
          <template #default="{ row }"><el-input v-model="row.reading" /></template>
        </el-table-column>
      </el-table>
      <el-form v-else label-width="100px" style="margin-top:8px">
        <el-form-item :label="t('meter.manual')">
          <DeviceSelect v-model="rf.deviceId" width="100%" testid="device-select" />
        </el-form-item>
        <el-form-item :label="t('meter.reading')" required>
          <el-input v-model="rf.reading" />
        </el-form-item>
        <el-alert type="warning" :closable="false" style="margin-top:4px"
                  :title="t('meter.noDeviceHint')" />
      </el-form>
      <template #footer>
        <el-button @click="recordVisible = false">{{ t('meter.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doRecord">{{ t('meter.recordBtn') }}</el-button>
      </template>
    </el-dialog>

    <!-- 导出 CSV 模板 -->
    <el-dialog v-model="exportVisible" :title="t('meter.exportTitle')" width="520px">
      <el-form label-width="90px">
        <el-form-item :label="t('meter.org')">
          <el-select v-model="ex.orgId" filterable clearable style="width:100%"
                     :placeholder="t('meter.selectOrg')" @change="loadExportSpaces">
            <el-option v-for="o in exOrgs" :key="o.id" :label="o.orgName"
                       :value="String(o.id)" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('meter.space')">
          <el-select v-model="ex.spaceId" filterable clearable style="width:100%"
                     :placeholder="t('meter.spaceHint')">
            <el-option v-for="s in exSpaces" :key="s.id" :label="s.label" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('meter.feeItem')" required>
          <el-select v-model="ex.feeItemId" style="width:100%">
            <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                       :label="m.itemName" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon
                :title="t('meter.exportHint')" />
      <template #footer>
        <el-button @click="exportVisible = false">{{ t('meter.cancel') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doExport">{{ t('meter.export') }}</el-button>
      </template>
    </el-dialog>

    <!-- 批量录入 / CSV 导入 -->
    <el-dialog v-model="batchVisible" :title="t('meter.batchTitle')" width="1180px">
      <div class="toolbar" style="margin-bottom:8px">
        <el-button size="small" type="primary" plain @click="openExport">{{ t('meter.exportTemplate') }}</el-button>
        <el-button size="small" @click="addBatchRow">{{ t('meter.addRow') }}</el-button>
        <el-upload :auto-upload="false" :limit="1" accept=".csv" :show-file-list="false"
                   :on-change="onCsv">
          <el-button size="small">{{ t('meter.importCsv') }}</el-button>
        </el-upload>
        <span class="muted" style="font-size:12px">
          {{ t('meter.batchHint') }}
        </span>
      </div>
      <el-table :data="batchRows" size="small" border max-height="380">
        <el-table-column :label="t('meter.org')" width="170">
          <template #default="{ row }">
            <el-select v-model="row.orgId" size="small" filterable clearable
                       style="width:100%" :placeholder="t('meter.searchName')"
                       @change="fillRowDevice(row)">
              <el-option v-for="o in orgOptions" :key="o.id" :label="o.orgName"
                         :value="String(o.id)" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column :label="t('meter.house')" width="200">
          <template #default="{ row }">
            <HouseSelect :model-value="row.houseId" :org-id="row.orgId" width="100%"
                         @update:model-value="(v) => onRowHouse(row, v)" />
          </template>
        </el-table-column>
        <el-table-column :label="t('meter.feeItem')" width="150">
          <template #default="{ row }">
            <el-select v-model="row.feeItemId" size="small" style="width:100%"
                       @change="fillRowDevice(row)">
              <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                         :label="m.itemName" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column :label="t('meter.deviceId')" width="180">
          <template #default="{ row }">
            <el-select v-model="row.deviceId" size="small" filterable remote clearable
                       :remote-method="(kw) => searchDevice(row, kw)"
                       :loading="row.deviceLoading" style="width:100%"
                       :placeholder="t('meter.searchDevice')"
                       @change="(v) => pickSearchDevice(row, v)">
              <el-option v-for="d in (row.deviceOptions || [])" :key="d.device_id"
                         :label="d.device_id + '（' + (d.device_name || '') + '）'"
                         :value="d.device_id" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="deviceName" :label="t('meter.deviceName')" width="170" />
        <el-table-column prop="deviceType" :label="t('meter.deviceType')" width="120" />
        <el-table-column label="读数" width="100">
          <template #default="{ row }"><el-input v-model="row.reading" size="small" /></template>
        </el-table-column>
        <el-table-column :label="t('meter.readingDate')" width="135">
          <template #default="{ row }">
            <el-date-picker v-model="row.readDate" type="date" value-format="YYYY-MM-DD"
                            size="small" style="width:100%" />
          </template>
        </el-table-column>
        <el-table-column label="" width="60">
          <template #default="{ $index }">
            <el-button link type="danger" @click="batchRows.splice($index, 1)">{{ t('meter.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-alert v-if="batchResult" :type="batchResult.failed ? 'warning' : 'success'"
                :closable="false" style="margin-top:8px"
                :title="'共 ' + batchResult.total + ' 行，成功 ' + batchResult.created
                  + '，失败 ' + batchResult.failed" />
      <template #footer>
        <el-button @click="batchVisible = false">{{ t('meter.close') }}</el-button>
        <el-button type="primary" :loading="saving" @click="doBatch">{{ t('meter.submit') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const houses = ref([])
const meterItems = ref([])
const recordVisible = ref(false)
const query = reactive({ pageNum: 1, pageSize: 20, houseId: '', feeItemId: '',
  orgId: '', billed: '' })
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
const meterSelected = ref([])
const orgOptions = ref([])

async function loadOrgs() {
  try {
    const d = await req.get('/orgs', { params: { pageNum: 1, pageSize: 500 } })
    orgOptions.value = (d && d.rows) || []
  } catch (e) { orgOptions.value = [] }
}

async function batchBill() {
  const ids = meterSelected.value.filter((r) => !r.billId).map((r) => r.id)
  if (!ids.length) { ElMessage.warning('请勾选未出账的记录'); return }
  await ElMessageBox.confirm('将为已选 ' + ids.length + ' 条读数生成账单，是否继续？',
    '确认批量出账', { type: 'warning' })
  try {
    const r = await req.post('/fin/meter-readings/bill-batch', ids)
    ElMessage.success('出账完成：成功 ' + r.billed + '，失败 ' + r.failed)
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '批量出账失败')
  }
}

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
    row.devices = (list || []).map((d) => ({
      deviceId: d.device_id,
      deviceName: d.device_name,
      deviceType: d.device_type,
      spaceName: d.space_name
    }))
    if (row.devices.length) {
      row.deviceId = row.devices[0].deviceId
      row.deviceName = row.devices[0].deviceName
      row.deviceType = row.devices[0].deviceType
    }
  } catch (e) { /* 忽略 */ }
}

function pickDevice(row) {
  const d = (row.devices || []).find((x) => x.deviceId === row.deviceId)
  row.deviceName = d ? d.deviceName : ''
  row.deviceType = d ? d.deviceType : ''
}

watch(() => [rf.houseId, rf.feeItemId], () => loadDevices())

function onRowHouse(row, v) {
  row.houseId = v
  fillRowDevice(row)
}

/** 按组织 + 设备名称/编号搜索设备 */
async function searchDevice(row, keyword) {
  if (!keyword) return
  row.deviceLoading = true
  try {
    const list = await req.get('/fin/meter-readings/devices-search', {
      params: { orgId: row.orgId || undefined, keyword }
    })
    row.deviceOptions = list || []
  } catch (e) { row.deviceOptions = [] } finally { row.deviceLoading = false }
}

/** 选中设备后回填房源、项目、名称、类型 */
function pickSearchDevice(row, deviceId) {
  const d = (row.deviceOptions || []).find((x) => x.device_id === deviceId)
  if (!d) return
  row.deviceName = d.device_name
  row.deviceType = d.device_type
  row.houseId = d.house_id
  if (d.fee_item_id) row.feeItemId = d.fee_item_id
  if (!row.orgId && d.org_id) row.orgId = String(d.org_id)
}

async function loadDevices() {
  devices.value = []
  deviceRows.value = []
  if (!rf.houseId || !rf.feeItemId) return
  try {
    const list = await req.get('/fin/meter-readings/devices',
      { params: { houseId: rf.houseId, feeItemId: rf.feeItemId } })
    // 后端返回 snake_case，前端表格用 camelCase
    const mapped = (list || []).map((d) => ({
      deviceId: d.device_id,
      deviceName: d.device_name,
      deviceType: d.device_type,
      spaceName: d.space_name
    }))
    devices.value = mapped
    deviceRows.value = mapped.map((d) => ({ ...d, reading: '' }))
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
    if (query.orgId) params.orgId = query.orgId
    if (query.billed !== '' && query.billed != null) params.billed = query.billed
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
  loadOrgs()
  load()
})
</script>
