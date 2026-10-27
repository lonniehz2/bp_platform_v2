# -*- coding: utf-8 -*-
"""设备批量绑定：三步向导（选择 → 校验预览 → 结果）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'DeviceBinding.vue')
s = io.open(p, encoding='utf-8').read()

# 工具栏加按钮
s = s.replace('''      <el-button type="primary" @click="loadHouses">搜索房源</el-button>''',
              '''      <el-button type="primary" @click="loadHouses">搜索房源</el-button>
      <el-button type="success" plain @click="openBatchBind" data-testid="device-batch-bind">
        批量绑定
      </el-button>''', 1)

# 弹窗（放在模板末尾前）
dialog = '''
    <!-- 设备批量绑定：选择 → 校验预览 → 结果 -->
    <el-dialog v-model="batchVisible" title="设备批量绑定" width="820px" @close="resetBatch">
      <el-steps :active="batchStep" simple style="margin-bottom:14px">
        <el-step title="选择文件" />
        <el-step title="校验预览" />
        <el-step title="绑定结果" />
      </el-steps>

      <div v-if="batchStep === 1">
        <el-alert type="info" :closable="false" show-icon
                  title="CSV 列顺序：房源编号, 设备编号（首行可为表头；设备会绑定到房源所在空间）" />
        <div style="margin:12px 0;display:flex;gap:8px;align-items:center">
          <el-button size="small" @click="downloadBindTemplate">下载模板</el-button>
          <span class="muted" style="font-size:12px">已绑定其它空间的设备会失败并给出原因</span>
        </div>
        <el-upload :auto-upload="false" :limit="1" accept=".csv"
                   :on-change="onBindFile" :file-list="bindFiles">
          <el-button type="primary" plain>选择 CSV 文件</el-button>
        </el-upload>
      </div>

      <div v-else-if="batchStep === 2">
        <el-alert :type="bindProblems.length ? 'warning' : 'success'" :closable="false" show-icon
                  :title="bindProblems.length
                    ? ('预览发现 ' + bindProblems.length + ' 处问题，可修正后重新选择')
                    : ('准备绑定 ' + bindRows.length + ' 行')" />
        <el-table :data="bindRows" size="small" border max-height="280" style="margin-top:8px">
          <el-table-column prop="line" label="行" width="60" />
          <el-table-column prop="houseCode" label="房源编号" width="170" />
          <el-table-column prop="deviceId" label="设备编号" width="190" />
        </el-table>
        <el-table v-if="bindProblems.length" :data="bindProblems" size="small" border
                  style="margin-top:8px" max-height="150">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="问题" />
        </el-table>
      </div>

      <div v-else>
        <el-alert :type="bindResult && bindResult.failed ? 'warning' : 'success'"
                  :closable="false" show-icon
                  :title="bindResult
                    ? ('共 ' + bindResult.total + ' 行，成功 ' + bindResult.success
                       + '，失败 ' + bindResult.failed)
                    : '绑定完成'" />
        <div v-if="bindResult" style="margin:10px 0">
          <el-button size="small" :disabled="!bindResult.failed" @click="exportBindErrors">
            导出失败行
          </el-button>
        </div>
        <el-table v-if="bindResult" :data="bindResult.rows" size="small" border max-height="260">
          <el-table-column prop="line" label="行" width="60" />
          <el-table-column prop="houseCode" label="房源编号" width="160" />
          <el-table-column prop="deviceId" label="设备编号" width="180" />
          <el-table-column label="结果" width="90">
            <template #default="{ row }">
              <el-tag size="small" :type="row.success ? 'success' : 'danger'">
                {{ row.success ? '成功' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="说明" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="batchVisible = false">关闭</el-button>
        <el-button v-if="batchStep === 2" @click="batchStep = 1">重新选择</el-button>
        <el-button v-if="batchStep === 2" type="primary" :loading="batchSaving"
                   :disabled="!bindRows.length || !!bindProblems.length" @click="doBatchBind">
          开始绑定
        </el-button>
        <el-button v-if="batchStep === 3" @click="loadDevices">刷新设备</el-button>
      </template>
    </el-dialog>
'''
idx = s.rfind('  </div>\n</template>')
if idx < 0:
    raise SystemExit('未找到模板结尾')
s = s[:idx] + dialog + s[idx:]

# 状态与方法
if 'const batchVisible' not in s:
    s = s.replace('''const bindVisible = ref(false)''', '''const batchVisible = ref(false)
const batchStep = ref(1)
const batchSaving = ref(false)
const bindFiles = ref([])
const bindRows = ref([])
const bindProblems = ref([])
const bindResult = ref(null)
let bindFile = null

function openBatchBind() {
  resetBatch()
  batchVisible.value = true
}

function resetBatch() {
  batchStep.value = 1
  bindFiles.value = []
  bindRows.value = []
  bindProblems.value = []
  bindResult.value = null
  batchSaving.value = false
  bindFile = null
}

function downloadBindTemplate() {
  const csv = '\\ufeff房源编号,设备编号\\nZZ-H-00001,LK00000001\\n'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备批量绑定模板.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

/** 选文件 → 解析 → 校验 → 进入预览 */
function onBindFile(file) {
  bindFile = file.raw
  bindFiles.value = [file]
  bindResult.value = null
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = String(e.target.result || '').replace(/^\\ufeff/, '')
    const lines = text.split(/\\r?\\n/).filter((x) => x.trim() !== '')
    if (!lines.length) {
      bindProblems.value = [{ line: 0, message: '文件为空' }]
      batchStep.value = 2
      return
    }
    let body = lines
    if (/房源编号|houseCode/i.test(lines[0])) {
      body = lines.slice(1)
    }
    const seenDevice = new Set()
    const seenPair = new Set()
    const problems = []
    bindRows.value = body.map((l, i) => {
      const line = i + (lines.length - body.length) + 1
      const cells = l.split(',').map((x) => (x || '').trim())
      const houseCode = cells[0] || ''
      const deviceId = cells[1] || ''
      if (!houseCode) problems.push({ line, message: '房源编号为空' })
      if (!deviceId) problems.push({ line, message: '设备编号为空' })
      if (deviceId && seenDevice.has(deviceId)) {
        problems.push({ line, message: '同一设备在文件中重复：' + deviceId })
      }
      if (deviceId) seenDevice.add(deviceId)
      const pair = houseCode + '|' + deviceId
      if (houseCode && deviceId && seenPair.has(pair)) {
        problems.push({ line, message: '同一「房源+设备」重复' })
      }
      seenPair.add(pair)
      return { line, houseCode, deviceId }
    })
    bindProblems.value = problems
    batchStep.value = 2
  }
  reader.readAsText(file.raw, 'utf-8')
}

/** 提交批量绑定 */
async function doBatchBind() {
  if (!bindRows.value.length) { ElMessage.warning('没有可绑定的数据'); return }
  batchSaving.value = true
  try {
    const r = await req.post('/devices/bind-batch', bindRows.value)
    bindResult.value = r || {}
    batchStep.value = 3
    ElMessage.success('绑定完成：成功 ' + (r?.success || 0) + '，失败 ' + (r?.failed || 0))
    loadDevices()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '批量绑定失败')
  } finally { batchSaving.value = false }
}

function exportBindErrors() {
  const rows = ((bindResult.value && bindResult.value.rows) || []).filter((x) => !x.success)
  const csv = '\\ufeff行号,房源编号,设备编号,原因\\n'
    + rows.map((x) => [x.line, x.houseCode, x.deviceId, String(x.message || '').replace(/,/g, '，')].join(','))
      .join('\\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '设备绑定失败行.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

const bindVisible = ref(false)''', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('设备批量绑定三步已加')
