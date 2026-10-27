# -*- coding: utf-8 -*-
"""设备管理：批量导入三步向导。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'Devices.vue')
s = io.open(p, encoding='utf-8').read()

# 工具栏按钮
s = s.replace('''      <el-button type="warning" plain :loading="syncing" @click="syncDevices">
        同步设备
      </el-button>''', '''      <el-button type="warning" plain :loading="syncing" @click="syncDevices">
        同步设备
      </el-button>
      <el-button type="warning" plain data-testid="device-import"
                 @click="openImport">批量导入</el-button>''', 1)

dialog = '''
    <!-- 设备批量导入 -->
    <el-dialog v-model="impVisible" title="设备批量导入" width="820px" @close="resetImport">
      <el-steps :active="impStep" simple style="margin-bottom:14px">
        <el-step title="选择文件" />
        <el-step title="校验预览" />
        <el-step title="导入结果" />
      </el-steps>

      <div v-if="impStep === 1">
        <el-alert type="info" :closable="false" show-icon
                  title="CSV 列：设备编号, 设备名称, 设备类型, 设备MAC, 房源编号(可空)" />
        <div class="muted" style="font-size:12px;margin:8px 0">
          设备类型可填：门锁 / 门禁 / 道闸 / 摄像头 / 电表 / 水表 / 燃气表 / 传感器（也支持英文码）
        </div>
        <div style="margin:12px 0;display:flex;gap:8px;align-items:center">
          <el-button size="small" @click="downloadDeviceTemplate">下载模板</el-button>
          <span class="muted" style="font-size:12px">设备编号重复会自动跳过</span>
        </div>
        <el-upload :auto-upload="false" :limit="1" accept=".csv"
                   :on-change="onImportFile" :file-list="impFiles">
          <el-button type="primary" plain>选择 CSV 文件</el-button>
        </el-upload>
      </div>

      <div v-else-if="impStep === 2">
        <el-alert :type="impProblems.length ? 'warning' : 'success'" :closable="false" show-icon
                  :title="impProblems.length
                    ? ('预览发现 ' + impProblems.length + ' 处问题，可修正后重新选择')
                    : ('准备导入 ' + impRows.length + ' 行')" />
        <el-table :data="impRows.slice(0, 8)" size="small" border max-height="240"
                  style="margin-top:8px">
          <el-table-column prop="line" label="行" width="60" />
          <el-table-column prop="deviceId" label="设备编号" width="170" />
          <el-table-column prop="deviceName" label="设备名称" min-width="140" />
          <el-table-column prop="typeLabel" label="类型" width="100" />
          <el-table-column prop="mac" label="MAC" width="160" />
          <el-table-column prop="houseCode" label="房源编号" width="140" />
        </el-table>
        <el-table v-if="impProblems.length" :data="impProblems" size="small" border
                  style="margin-top:8px" max-height="140">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="问题" />
        </el-table>
      </div>

      <div v-else>
        <el-alert :type="impResult && impResult.errors && impResult.errors.length ? 'warning' : 'success'"
                  :closable="false" show-icon
                  :title="impResult
                    ? ('共 ' + impResult.total + ' 行，成功 ' + impResult.created
                       + '，跳过 ' + impResult.skipped)
                    : '导入完成'" />
        <div style="margin:10px 0">
          <el-button size="small"
                     :disabled="!impResult || !impResult.errors || !impResult.errors.length"
                     @click="exportImpErrors">导出失败行</el-button>
        </div>
        <el-table v-if="impResult && impResult.errors" :data="impResult.errors"
                  size="small" border max-height="220">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="原因" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="impVisible = false">关闭</el-button>
        <el-button v-if="impStep === 2" @click="impStep = 1">重新选择</el-button>
        <el-button v-if="impStep === 3" @click="load">刷新列表</el-button>
        <el-button v-if="impStep === 2" type="primary" :loading="impSaving"
                   :disabled="!impFile || !!impProblems.length" @click="doImport">
          开始导入
        </el-button>
      </template>
    </el-dialog>
'''
idx = s.rfind('</template>')
if idx < 0:
    raise SystemExit('模板结尾未找到')
s = s[:idx] + dialog + s[idx:]

if 'const impStep' not in s:
    s = s.replace('''const evVisible = ref(false)''', '''const impVisible = ref(false)
const impStep = ref(1)
const impSaving = ref(false)
const impFiles = ref([])
const impRows = ref([])
const impProblems = ref([])
const impResult = ref(null)
let impFile = null

const DEVICE_TYPE_LABEL = {
  LOCK: '门锁', ACCESS: '门禁', BARRIER: '道闸', CAMERA: '摄像头',
  ELEC_METER: '电表', WATER_METER: '水表', GAS_METER: '燃气表', SENSOR: '传感器'
}
const TYPE_BY_TEXT = {
  门锁: 'LOCK', 智能锁: 'LOCK', 门禁: 'ACCESS', 道闸: 'BARRIER', 摄像头: 'CAMERA',
  视频: 'CAMERA', 电表: 'ELEC_METER', 水表: 'WATER_METER', 燃气表: 'GAS_METER',
  气表: 'GAS_METER', 传感器: 'SENSOR'
}

function openImport() {
  resetImport()
  impVisible.value = true
}

function resetImport() {
  impStep.value = 1
  impFiles.value = []
  impRows.value = []
  impProblems.value = []
  impResult.value = null
  impSaving.value = false
  impFile = null
}

function downloadDeviceTemplate() {
  const csv = '\\ufeff设备编号,设备名称,设备类型,设备MAC,房源编号\\n'
    + 'LK00000001,1栋101门锁,门锁,AA:BB:CC:DD:EE:01,H8063501\\n'
    + 'EM00000001,1栋101电表,电表,AA:BB:CC:DD:EE:02,\\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备导入模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

/** 简单 CSV 解析（支持引号） */
function parseCsvText(text) {
  const clean = text.replace(/^\\ufeff/, '')
  const rows = []
  let cur = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < clean.length; i++) {
    const ch = clean[i]
    if (quoted) {
      if (ch === '"' && clean[i + 1] === '"') { cell += '"'; i++ }
      else if (ch === '"') quoted = false
      else cell += ch
    } else if (ch === '"') quoted = true
    else if (ch === ',') { cur.push(cell); cell = '' }
    else if (ch === '\\n') { cur.push(cell); rows.push(cur); cur = []; cell = '' }
    else if (ch !== '\\r') cell += ch
  }
  if (cell !== '' || cur.length) { cur.push(cell); rows.push(cur) }
  return rows.filter((r) => r.some((x) => (x || '').trim() !== ''))
}

function onImportFile(file) {
  impFile = file.raw
  impFiles.value = [file]
  impResult.value = null
  const reader = new FileReader()
  reader.onload = (e) => {
    const all = parseCsvText(String(e.target.result || ''))
    if (!all.length) {
      impProblems.value = [{ line: 0, message: '文件为空' }]
      impStep.value = 2
      return
    }
    let body = all
    if (/设备编号|deviceId/i.test(all[0].join(','))) body = all.slice(1)
    const seen = new Set()
    const problems = []
    impRows.value = body.map((cells, i) => {
      const line = i + (all.length - body.length) + 1
      const deviceId = (cells[0] || '').trim()
      const deviceName = (cells[1] || '').trim()
      const typeText = (cells[2] || '').trim()
      const mac = (cells[3] || '').trim()
      const houseCode = (cells[4] || '').trim()
      const code = TYPE_BY_TEXT[typeText] || (DEVICE_TYPE_LABEL[typeText] ? typeText : null)
      if (!deviceId) problems.push({ line, message: '设备编号为空' })
      else if (seen.has(deviceId)) problems.push({ line, message: '文件内设备编号重复：' + deviceId })
      else seen.add(deviceId)
      if (!typeText) problems.push({ line, message: '设备类型为空' })
      else if (!code) problems.push({ line, message: '无法识别的设备类型：' + typeText })
      return {
        line, deviceId, deviceName, mac, houseCode,
        typeLabel: code ? DEVICE_TYPE_LABEL[code] : typeText
      }
    })
    impProblems.value = problems
    impStep.value = 2
  }
  reader.readAsText(file.raw, 'utf-8')
}

async function doImport() {
  if (!impFile) { ElMessage.warning('请选择 CSV 文件'); return }
  impSaving.value = true
  try {
    const fd = new FormData()
    fd.append('file', impFile)
    const r = await req.post('/devices/import', fd,
      { headers: { 'Content-Type': 'multipart/form-data' } })
    impResult.value = r || {}
    impStep.value = 3
    ElMessage.success('导入完成：成功 ' + (r?.created || 0) + '，跳过 ' + (r?.skipped || 0))
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导入失败')
  } finally { impSaving.value = false }
}

function exportImpErrors() {
  const rows = (impResult.value && impResult.value.errors) || []
  const csv = '\\ufeff行号,原因\\n'
    + rows.map((x) => x.line + ',' + String(x.message || '').replace(/,/g, '，')).join('\\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备导入失败行.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

const evVisible = ref(false)''', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('设备导入三步已加')
