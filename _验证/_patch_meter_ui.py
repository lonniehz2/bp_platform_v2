# -*- coding: utf-8 -*-
"""抄表：设备感知单条 + 批量 + CSV 导入；移除账单页抄表入口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')


def patch(p, pairs):
    s = io.open(p, encoding='utf-8').read()
    for old, new, label in pairs:
        if old not in s:
            print('  ! 未匹配:', label)
            continue
        s = s.replace(old, new, 1)
        print('  ✔', label)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    return s


# ---------- Bills：移除抄表录入入口 ----------
p = os.path.join(V, 'Bills.vue')
patch(p, [
    ('''        <el-button type="primary" plain @click="openMeter" data-testid="meter-reading">抄表录入</el-button>
''', '', '移除抄表按钮'),
])

# ---------- MeterReadings ----------
p = os.path.join(V, 'MeterReadings.vue')
patch(p, [
    ('''      <el-button type="success" plain @click="openRecord" data-testid="meter-new">
        录入读数
      </el-button>''',
     '''      <el-button type="success" plain @click="openRecord" data-testid="meter-new">
        录入读数
      </el-button>
      <el-button type="primary" plain @click="openBatch" data-testid="meter-batch">
        批量录入/导入
      </el-button>''', '批量入口'),

    # 单条录入对话框：设备按房源+项目带出
    ('''    <!-- 录入读数 -->
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
    </el-dialog>''',
     '''    <!-- 单条录入：按房源 + 计量项目带出设备，多设备逐台录入 -->
    <el-dialog v-model="recordVisible" title="录入抄表读数" width="640px">
      <el-form :model="rf" label-width="100px">
        <el-form-item label="房源" required>
          <el-select v-model="rf.houseId" filterable style="width:100%" placeholder="选择房源"
                     @change="loadDevices">
            <el-option v-for="h in houses" :key="h.id" :value="h.id"
                       :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'" />
          </el-select>
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
        <el-table-column prop="deviceType" label="设备类型" width="120" />
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
        <div class="muted" style="font-size:12px">未找到绑定设备，可手工选择设备或留空按人工录入</div>
      </el-form>
      <template #footer>
        <el-button @click="recordVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doRecord">录入</el-button>
      </template>
    </el-dialog>

    <!-- 批量录入 / CSV 导入 -->
    <el-dialog v-model="batchVisible" title="批量录入 / 导入抄表" width="920px">
      <div class="toolbar" style="margin-bottom:8px">
        <el-button size="small" @click="downloadTemplate">下载模板</el-button>
        <el-button size="small" @click="addBatchRow">添加一行</el-button>
        <el-upload :auto-upload="false" :limit="1" accept=".csv" :show-file-list="false"
                   :on-change="onCsv">
          <el-button size="small">导入 CSV</el-button>
        </el-upload>
        <span class="muted" style="font-size:12px">
          CSV 列：房源编号, 计量项目, 设备编号(可空), 读数, 抄表日期
        </span>
      </div>
      <el-table :data="batchRows" size="small" border max-height="380">
        <el-table-column label="房源" width="230">
          <template #default="{ row }">
            <el-select v-model="row.houseId" filterable size="small" style="width:100%">
              <el-option v-for="h in houses" :key="h.id" :value="h.id"
                         :label="(h.houseName || h.houseCode) + '（' + h.houseCode + '）'" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="计量项目" width="180">
          <template #default="{ row }">
            <el-select v-model="row.feeItemId" size="small" style="width:100%">
              <el-option v-for="m in meterItems" :key="m.id" :value="m.id"
                         :label="m.itemName" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="设备编号" width="170">
          <template #default="{ row }"><el-input v-model="row.deviceId" size="small" /></template>
        </el-table-column>
        <el-table-column label="读数" width="120">
          <template #default="{ row }"><el-input v-model="row.reading" size="small" /></template>
        </el-table-column>
        <el-table-column label="抄表日期" width="140">
          <template #default="{ row }">
            <el-date-picker v-model="row.readDate" type="date" value-format="YYYY-MM-DD"
                            size="small" style="width:100%" />
          </template>
        </el-table-column>
        <el-table-column label="" width="70">
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
    </el-dialog>''', '抄表对话框'),
])

# ---------- script ----------
s = io.open(p, encoding='utf-8').read()
if 'deviceRows' not in s:
    s = s.replace('''const rf = reactive({ houseId: '', feeItemId: '', reading: '', readDate: '', deviceId: '' })''',
                  '''const rf = reactive({ houseId: '', feeItemId: '', reading: '', readDate: '', deviceId: '' })
const devices = ref([])
const deviceRows = ref([])
const batchVisible = ref(false)
const batchRows = ref([])
const batchResult = ref(null)

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
  const csv = '\\ufeff房源编号,计量项目,设备编号,读数,抄表日期\\n'
    + 'H8063501,电费,DEMO-ELEC-00001,1200.5,2026-10-28\\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '抄表导入模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

function parseCsv(text) {
  const rows = []
  text.replace(/^\\ufeff/, '').split(/\\r?\\n/).forEach((line) => {
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
    const body = /房源编号/.test(all[0].join(',')) ? all.slice(1) : all
    batchRows.value = body.map((c) => {
      const house = houses.value.find((h) => String(h.houseCode) === c[0]
        || String(h.houseName) === c[0])
      const item = meterItems.value.find((m) => m.itemName === c[1]
        || String(m.itemCode) === c[1])
      return { houseId: house ? house.id : '', feeItemId: item ? item.id : '',
        deviceId: c[2] || '', reading: c[3] || '', readDate: c[4] || '' }
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
}''', 1)

    # openRecord 重置设备；doRecord 支持多设备
    s = s.replace('''function openRecord() {
  Object.assign(rf, { houseId: query.houseId || '', feeItemId: query.feeItemId || '',
    reading: '', readDate: new Date().toISOString().slice(0, 10), deviceId: '' })
  recordVisible.value = true
}''', '''function openRecord() {
  Object.assign(rf, { houseId: query.houseId || '', feeItemId: query.feeItemId || '',
    reading: '', readDate: new Date().toISOString().slice(0, 10), deviceId: '' })
  devices.value = []
  deviceRows.value = []
  recordVisible.value = true
  loadDevices()
}''', 1)

    s = s.replace('''async function doRecord() {
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
}''', '''async function doRecord() {
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
}''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 抄表设备/批量/导入脚本')
