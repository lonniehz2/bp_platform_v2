# -*- coding: utf-8 -*-
"""房源批量导入：选择文件 → 校验预览 → 提交结果 三步。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, 'frontend', 'src', 'views', 'Houses.vue')
s = io.open(p, encoding='utf-8').read()

start = s.find('    <!-- 批量导入房源（CSV 迁移用） -->')
end = s.find('</el-dialog>', start) + len('</el-dialog>')
if start < 0:
    raise SystemExit('未找到导入弹窗')

dialog = '''    <!-- 批量导入房源（CSV）：选择 → 校验预览 → 提交 -->
    <el-dialog v-model="importVisible" title="批量导入房源" width="820px"
               @close="resetImport">
      <el-steps :active="importStep" simple style="margin-bottom:14px">
        <el-step title="选择文件" />
        <el-step title="校验预览" />
        <el-step title="提交结果" />
      </el-steps>

      <div v-if="importStep === 1">
        <el-alert type="info" :closable="false" show-icon
                  title="CSV 列顺序：组织编码, 空间编码, 房源编号, 房源名称, 房源类型, 用途, 建筑面积(㎡), 租金标准, 计价单位, 房源状态" />
        <div style="margin:12px 0;display:flex;gap:8px;align-items:center">
          <el-button size="small" @click="downloadTemplate">下载模板</el-button>
          <span class="muted" style="font-size:12px">
            首行可为表头；编号重复的行会被跳过并给出原因
          </span>
        </div>
        <el-upload :auto-upload="false" :limit="1" accept=".csv"
                   :on-change="onImportFile" :file-list="importFiles">
          <el-button type="primary" plain>选择 CSV 文件</el-button>
        </el-upload>
      </div>

      <div v-else-if="importStep === 2">
        <el-alert :type="parseProblems.length ? 'warning' : 'success'" :closable="false" show-icon
                  :title="parseProblems.length
                    ? ('预览发现 ' + parseProblems.length + ' 处问题，可修正文件后重新选择')
                    : ('文件可导入：' + parsedRows.length + ' 行，列数 ' + parsedHeaders.length)" />
        <div class="muted" style="font-size:12px;margin:8px 0">
          下表为前 8 行预览；点击「开始导入」后由后端逐行二次校验，失败行会列在下一步。
        </div>
        <el-table :data="parsedRows.slice(0, 8)" size="small" border max-height="240">
          <el-table-column prop="line" label="行" width="60" />
          <el-table-column v-for="(h, i) in parsedHeaders.slice(0, 10)" :key="i"
                           :label="h || ('列' + (i + 1))" min-width="110"
                           show-overflow-tooltip>
            <template #default="{ row }">{{ (row.cells || [])[i] }}</template>
          </el-table-column>
        </el-table>
        <el-table v-if="parseProblems.length" :data="parseProblems" size="small" border
                  style="margin-top:8px" max-height="160">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="问题" />
        </el-table>
      </div>

      <div v-else>
        <el-alert :type="importResult && importResult.skipped ? 'warning' : 'success'"
                  :closable="false" show-icon
                  :title="importResult
                    ? ('共 ' + importResult.total + ' 行，成功 ' + importResult.created
                       + '，跳过 ' + importResult.skipped)
                    : '导入完成'" />
        <div v-if="importResult" style="margin:10px 0;display:flex;gap:8px">
          <el-button size="small" :disabled="!importResult.errors || !importResult.errors.length"
                     @click="exportImportErrors">导出失败行</el-button>
          <span class="muted" style="font-size:12px">失败行修正后可再次导入，成功行不会被重复创建</span>
        </div>
        <el-table v-if="importResult && importResult.errors && importResult.errors.length"
                  :data="importResult.errors" size="small" border max-height="220">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="原因" />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="importVisible = false">关闭</el-button>
        <el-button v-if="importStep > 1" @click="importStep = 1">重新选择</el-button>
        <el-button v-if="importStep === 3" @click="load">刷新列表</el-button>
        <el-button v-if="importStep === 2" type="primary" :loading="saving"
                   :disabled="!importFile || !!parseProblems.length" @click="doImport">
          开始导入
        </el-button>
      </template>
    </el-dialog>'''

s = s[:start] + dialog + s[end:]

# 状态与解析逻辑
if 'const importStep' not in s:
    s = s.replace('''const importResult = ref(null)''', '''const importResult = ref(null)
const importStep = ref(1)
const parsedRows = ref([])
const parsedHeaders = ref([])
const parseProblems = ref([])

/** 简单 CSV 解析：支持引号包裹、CRLF、BOM */
function parseCsv(text) {
  const clean = text.replace(/^\\ufeff/, '')
  const rows = []
  let cur = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < clean.length; i++) {
    const ch = clean[i]
    if (quoted) {
      if (ch === '"' && clean[i + 1] === '"') { cell += '"'; i++ }
      else if (ch === '"') { quoted = false }
      else { cell += ch }
    } else if (ch === '"') { quoted = true }
    else if (ch === ',') { cur.push(cell); cell = '' }
    else if (ch === '\\n') { cur.push(cell); rows.push(cur); cur = []; cell = '' }
    else if (ch === '\\r') { /* 忽略 */ }
    else { cell += ch }
  }
  if (cell !== '' || cur.length) { cur.push(cell); rows.push(cur) }
  return rows.filter((r) => r.some((x) => (x || '').trim() !== ''))
}

/** 选文件后解析并进入预览 */
function onImportFile(file) {
  importFile = file.raw
  importFiles.value = [file]
  importResult.value = null
  parsedRows.value = []
  parsedHeaders.value = []
  parseProblems.value = []
  const reader = new FileReader()
  reader.onload = (e) => {
    const all = parseCsv(String(e.target.result || ''))
    if (!all.length) {
      parseProblems.value = [{ line: 0, message: '文件为空' }]
      importStep.value = 2
      return
    }
    let body = all
    const first = (all[0] || []).join(',')
    if (/房源编号|houseCode/i.test(first)) {
      parsedHeaders.value = all[0].map((x) => (x || '').trim())
      body = all.slice(1)
    } else {
      parsedHeaders.value = ['组织编码', '空间编码', '房源编号', '房源名称', '房源类型',
        '用途', '建筑面积', '租金标准', '计价单位', '房源状态']
    }
    const seen = new Set()
    const problems = []
    parsedRows.value = body.map((cells, idx) => {
      const line = idx + (all.length - body.length) + 1
      if (cells.length < 10) {
        problems.push({ line, message: '列数不足（' + cells.length + ' 列，应为 10 列）' })
      }
      const code = (cells[2] || '').trim()
      if (!code) problems.push({ line, message: '房源编号为空' })
      else if (seen.has(code)) problems.push({ line, message: '文件内房源编号重复：' + code })
      else seen.add(code)
      if (!(cells[3] || '').trim()) problems.push({ line, message: '房源名称为空' })
      if (!(cells[6] || '').trim()) problems.push({ line, message: '建筑面积为空' })
      return { line, cells }
    })
    parseProblems.value = problems
    importStep.value = 2
  }
  reader.readAsText(file.raw, 'utf-8')
}

/** 导出失败行 */
function exportImportErrors() {
  const errs = (importResult.value && importResult.value.errors) || []
  const csv = '\\ufeff行号,原因\\n' + errs.map((x) => x.line + ',' + String(x.message).replace(/,/g, '，')).join('\\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = '房源导入失败行.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

function resetImport() {
  importStep.value = 1
  parsedRows.value = []
  parsedHeaders.value = []
  parseProblems.value = []
  importResult.value = null
  importFiles.value = []
  importFile = null
}''', 1)

# doImport 成功后进入第 3 步
s = s.replace('''    importResult.value = r || {}
    ElMessage.success(`导入完成：成功 ${r?.created || 0}，跳过 ${r?.skipped || 0}`)
    load()''', '''    importResult.value = r || {}
    importStep.value = 3
    ElMessage.success(`导入完成：成功 ${r?.created || 0}，跳过 ${r?.skipped || 0}`)
    load()''', 1)

# 旧的 onImportFile 定义去重（新函数已插入，旧的仍存在）
old = '''function onImportFile(file) {
  importFile = file.raw
  importFiles.value = [file]
  importResult.value = null
}'''
if old in s:
    s = s.replace(old, '', 1)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('房源导入三步已实现')
