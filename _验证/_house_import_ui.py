# -*- coding: utf-8 -*-
"""收尾房源导入：修正表头识别 + 前端「批量导入」入口。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 1) 后端：表头识别兼容 HOUSE_CODE ----------
P = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp',
                 'asset', 'service', 'impl', 'HouseServiceImpl.java')
s = io.open(P, encoding='utf-8').read()
old = 'if (lineNo == 1 && line.toLowerCase().contains("housecode")) {'
new = 'if (lineNo == 1\n                        && line.toLowerCase().replace("_", "").replace("-", "")\n                                .contains("housecode")) {'
if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('表头识别已修正')

# ---------- 2) 前端：房源台账加「批量导入」 ----------
V = os.path.join(ROOT, 'frontend', 'src', 'views', 'Houses.vue')
s = io.open(V, encoding='utf-8').read()

if 'importVisible' not in s:
    anchor = '<el-button type="success" @click="openCreate">新增房源</el-button>'
    if anchor not in s:
        print('未找到新增房源按钮，跳过前端')
    else:
        s = s.replace(anchor, anchor + '''
        <el-button type="warning" plain @click="importVisible = true"
                   data-testid="house-import">批量导入</el-button>''', 1)

        dialog = '''
    <!-- 批量导入房源（CSV 迁移用） -->
    <el-dialog v-model="importVisible" title="批量导入房源" width="620px">
      <el-alert type="info" :closable="false" show-icon
                title="CSV 列顺序：组织编码, 空间编码, 房源编号, 房源名称, 房源类型, 用途, 面积, 租金标准, 租金单位, 状态" />
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
      <div v-if="importResult" style="margin-top:12px">
        <el-alert :type="importResult.skipped ? 'warning' : 'success'" :closable="false"
                  :title="`共 ${importResult.total} 行，成功 ${importResult.created}，跳过 ${importResult.skipped}`" />
        <el-table v-if="importResult.errors && importResult.errors.length"
                  :data="importResult.errors" size="small" border max-height="220"
                  style="margin-top:8px">
          <el-table-column prop="line" label="行号" width="80" />
          <el-table-column prop="message" label="原因" />
        </el-table>
      </div>
      <template #footer>
        <el-button @click="importVisible = false">关闭</el-button>
        <el-button type="primary" :loading="saving" :disabled="!importFiles.length"
                   @click="doImport">开始导入</el-button>
      </template>
    </el-dialog>
'''
        idx = s.rfind('</template>')
        s = s[:idx] + dialog + s[idx:]

        script = '''
/** 批量导入房源（CSV） */
const importVisible = ref(false)
const importFiles = ref([])
const importResult = ref(null)
let importFile = null

function onImportFile(file) {
  importFile = file.raw
  importFiles.value = [file]
  importResult.value = null
}

function downloadTemplate() {
  const header = 'ORGANIZATION_CODE,SPACE_CODE,HOUSE_CODE,HOUSE_NAME,HOUSE_TYPE,'
    + 'USE_TYPE,AREA,RENT,RENT_UNIT,STATUS\\n'
  const sample = 'DEMO-P1,P1-R1,HOUSE-001,示例房源1,PUBLIC_RENTAL,CIVIL,55,15,'
    + 'AREA_MONTH,VACANT\\n'
  const blob = new Blob(['\\ufeff' + header + sample], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = 'house-import-template.csv'
  a.click()
  URL.revokeObjectURL(a.href)
}

async function doImport() {
  if (!importFile) { ElMessage.warning('请选择 CSV 文件'); return }
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('file', importFile)
    const r = await req.post('/houses/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    importResult.value = r || {}
    ElMessage.success(`导入完成：成功 ${r?.created || 0}，跳过 ${r?.skipped || 0}`)
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '导入失败')
  } finally { saving.value = false }
}
'''
        anchor2 = 'onMounted('
        i = s.find(anchor2)
        s = s[:i] + script + '\n' + s[i:]

        # 确保 req 与 saving 可用
        if "import req from '@/api/request'" not in s:
            s = s.replace("import { houseApi } from '@/api/modules'",
                          "import { houseApi } from '@/api/modules'\nimport req from '@/api/request'", 1)
        if 'const saving = ref(' not in s:
            s = s.replace("const loading = ref(false)", "const loading = ref(false)\nconst saving = ref(false)", 1)

        io.open(V, 'w', encoding='utf-8', newline='').write(s)
        print('Houses.vue：已加批量导入入口')
else:
    print('前端已存在')
