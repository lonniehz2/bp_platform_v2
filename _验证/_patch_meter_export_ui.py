# -*- coding: utf-8 -*-
"""抄表：批量行自动带出设备名称/类型；导出CSV选择组织/空间/项目。"""
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


p = os.path.join(V, 'MeterReadings.vue')
s = io.open(p, encoding='utf-8').read()

# ---------- 批量弹窗：替换工具栏与表格 ----------
if '导出CSV' not in s:
    s = s.replace('''      <div class="toolbar" style="margin-bottom:8px">
        <el-button size="small" @click="downloadTemplate">下载模板</el-button>
        <el-button size="small" @click="addBatchRow">添加一行</el-button>
        <el-upload :auto-upload="false" :limit="1" accept=".csv" :show-file-list="false"
                   :on-change="onCsv">
          <el-button size="small">导入 CSV</el-button>
        </el-upload>
        <span class="muted" style="font-size:12px">
          CSV 列：房源编号, 计量项目, 设备编号(可空), 读数, 抄表日期
        </span>
      </div>''', '''      <div class="toolbar" style="margin-bottom:8px">
        <el-button size="small" type="primary" plain @click="openExport">导出 CSV 模板</el-button>
        <el-button size="small" @click="addBatchRow">添加一行</el-button>
        <el-upload :auto-upload="false" :limit="1" accept=".csv" :show-file-list="false"
                   :on-change="onCsv">
          <el-button size="small">导入 CSV</el-button>
        </el-upload>
        <span class="muted" style="font-size:12px">
          导出 → 填读数 → 原样导入（列：组织,空间,房源编号,房源名称,计费项目,设备编号,设备名称,设备类型,读数,抄表日期）
        </span>
      </div>''', 1)
    # 表格：设备列改为可带出名称/类型
    s = s.replace('''        <el-table-column label="设备编号" width="170">
          <template #default="{ row }"><el-input v-model="row.deviceId" size="small" /></template>
        </el-table-column>''', '''        <el-table-column label="设备编号" width="180">
          <template #default="{ row }">
            <el-select v-if="row.devices && row.devices.length > 1" v-model="row.deviceId"
                       size="small" style="width:100%" @change="pickDevice(row)">
              <el-option v-for="d in row.devices" :key="d.device_id"
                         :label="d.device_id" :value="d.device_id" />
            </el-select>
            <el-input v-else v-model="row.deviceId" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="deviceName" label="设备名称" min-width="150" />
        <el-table-column prop="deviceType" label="设备类型" width="120" />''', 1)
    # 行内房源/项目变更 -> 带出设备
    s = s.replace('''            <el-select v-model="row.houseId" filterable size="small" style="width:100%">''',
                  '''            <el-select v-model="row.houseId" filterable size="small" style="width:100%"
                       @change="fillRowDevice(row)">''', 1)
    s = s.replace('''            <el-select v-model="row.feeItemId" size="small" style="width:100%">''',
                  '''            <el-select v-model="row.feeItemId" size="small" style="width:100%"
                       @change="fillRowDevice(row)">''', 1)
    # 导出对话框（插入到批量弹窗后）
    s = s.replace('''    <!-- 批量录入 / CSV 导入 -->''', '''    <!-- 导出 CSV 模板 -->
    <el-dialog v-model="exportVisible" title="导出抄表 CSV" width="520px">
      <el-form label-width="90px">
        <el-form-item label="组织">
          <OrgSelect v-model="ex.orgId" width="100%" testid="meter-ex-org" />
        </el-form-item>
        <el-form-item label="空间">
          <SpaceSelect v-model="ex.spaceId" :org-id="ex.orgId" width="100%"
                       testid="meter-ex-space" placeholder="选择空间（含下级）" />
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

    <!-- 批量录入 / CSV 导入 -->''', 1)

    if 'OrgSelect' not in s:
        s = s.replace("import DeviceSelect from '@/components/DeviceSelect.vue'",
                      "import DeviceSelect from '@/components/DeviceSelect.vue'\n"
                      "import OrgSelect from '@/components/OrgSelect.vue'\n"
                      "import SpaceSelect from '@/components/SpaceSelect.vue'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 批量/导出界面')

# ---------- 脚本 ----------
s = io.open(p, encoding='utf-8').read()
if 'const exportVisible' not in s:
    s = s.replace('''const batchResult = ref(null)''', '''const batchResult = ref(null)
const exportVisible = ref(false)
const ex = reactive({ orgId: '', spaceId: '', feeItemId: '' })

function openExport() {
  ex.feeItemId = query.feeItemId || ''
  ex.orgId = ''
  ex.spaceId = ''
  exportVisible.value = true
}

function csvCell(v) {
  const t = v == null ? '' : String(v)
  return /[",\\n]/.test(t) ? '"' + t.replace(/"/g, '""') + '"' : t
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
    const blob = new Blob(['\\ufeff' + lines.join('\\n')], { type: 'text/csv;charset=utf-8' })
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
}''', 1)

    # 新行带 devices 字段
    s = s.replace('''    batchRows.value.push({ houseId: query.houseId || '', feeItemId: query.feeItemId || '',
    deviceId: '', reading: '', readDate: new Date().toISOString().slice(0, 10) })''',
                  '''    batchRows.value.push({ houseId: query.houseId || '', feeItemId: query.feeItemId || '',
    deviceId: '', deviceName: '', deviceType: '', devices: [],
    reading: '', readDate: new Date().toISOString().slice(0, 10) })''', 1)

    # 导入解析：按表头映射并可回填设备名称/类型
    s = s.replace('''function onCsv(file) {
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
}''', '''function onCsv(file) {
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
}''', 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔ 导出/批量带出脚本')
