# -*- coding: utf-8 -*-
"""配租页补「新建批次」与「批次加房源」入口（后端接口已存在）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__) if False else os.path.abspath(__file__), '..'))
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Allocations.vue')

s = io.open(P, encoding='utf-8').read()
changed = []

# 1) 工具栏加「新建批次」
if 'openBatchCreate' not in s:
    m = re.search(r'(<div class="toolbar">\s*\n\s*<h3[^>]*>[^<]*</h3>[\s\S]{0,300}?)(<div class="spacer" />)', s)
    if m:
        s = s[:m.end(1)] + ('<el-button type="success" @click="openBatchCreate" '
                            'data-testid="batch-create">新建批次</el-button>\n        ') + s[m.end(1):]
        changed.append('工具栏按钮')

# 2) 行内加「加房源」
if 'openAddHouses(row)' not in s:
    s = re.sub(r'(<el-button link type="primary" @click="runLottery\(row\)">摇号</el-button>)',
               r'<el-button link type="primary" @click="openAddHouses(row)" '
               r'data-testid="batch-add-house">加房源</el-button>\n            \1', s, count=1)
    if 'batch-add-house' in s:
        changed.append('行内加房源')

# 3) 弹窗
dialogs = '''
    <!-- 新建批次 -->
    <el-dialog v-model="batchCreateVisible" title="新建配租批次" width="560px">
      <el-form :model="bf" label-width="110px">
        <el-form-item label="批次名称" required>
          <el-input v-model="bf.batchName" placeholder="如：2026 年第一批公租房配租" />
        </el-form-item>
        <el-form-item label="保障类型" required>
          <el-select v-model="bf.securityType" style="width:100%">
            <el-option label="公租房" value="PUBLIC" />
            <el-option label="经适房" value="AFFORDABLE" />
            <el-option label="人才房" value="TALENT" />
            <el-option label="廉租房" value="LOW_RENT" />
          </el-select>
        </el-form-item>
        <el-form-item label="组织 ID">
          <el-input v-model="bf.orgId" placeholder="可空" />
        </el-form-item>
        <el-form-item label="摇号种子">
          <el-input v-model="bf.seed" placeholder="可空，填了可复现摇号结果" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchCreateVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doCreateBatch">创建</el-button>
      </template>
    </el-dialog>

    <!-- 批次加房源 -->
    <el-dialog v-model="addHouseVisible" :title="`向批次「${addHouseBatch?.batchName || ''}」加入房源`"
               width="560px">
      <el-alert type="info" :closable="false" show-icon
                title="输入房源 ID，多个用英文逗号分隔；房源需为「空置可租」状态" />
      <el-input v-model="houseIdsText" type="textarea" :rows="4" style="margin-top:10px"
                placeholder="1000000000000012161,1000000000000012159" />
      <template #footer>
        <el-button @click="addHouseVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doAddHouses">加入</el-button>
      </template>
    </el-dialog>
'''
if 'batchCreateVisible' not in s:
    idx = s.rfind('</template>')
    s = s[:idx] + dialogs + s[idx:]
    changed.append('弹窗')

# 4) 脚本
script = '''
/** 新建批次 / 批次加房源（此前只能看列表，无法从界面建批次） */
const batchCreateVisible = ref(false)
const addHouseVisible = ref(false)
const addHouseBatch = ref(null)
const houseIdsText = ref('')
const bf = reactive({ batchName: '', securityType: 'PUBLIC', orgId: '', seed: '' })

function openBatchCreate() {
  Object.assign(bf, { batchName: '', securityType: 'PUBLIC', orgId: '', seed: '' })
  batchCreateVisible.value = true
}

async function doCreateBatch() {
  if (!bf.batchName) { ElMessage.warning('请填写批次名称'); return }
  saving.value = true
  try {
    await req.post('/allocation/batches', {
      batchName: bf.batchName,
      securityType: bf.securityType,
      orgId: bf.orgId || undefined,
      seed: bf.seed || undefined
    })
    ElMessage.success('批次已创建')
    batchCreateVisible.value = false
    load()
  } finally { saving.value = false }
}

function openAddHouses(row) {
  addHouseBatch.value = row
  houseIdsText.value = ''
  addHouseVisible.value = true
}

async function doAddHouses() {
  const ids = houseIdsText.value.split(/[,，\\s]+/).map((x) => x.trim()).filter(Boolean)
  if (!ids.length) { ElMessage.warning('请填写房源 ID'); return }
  saving.value = true
  try {
    await req.post(`/allocation/batches/${addHouseBatch.value.id}/houses`, { houseIds: ids })
    ElMessage.success(`已加入 ${ids.length} 个房源`)
    addHouseVisible.value = false
    load()
  } finally { saving.value = false }
}
'''
if 'function openBatchCreate' not in s:
    anchor = 'onMounted(load)'
    s = s.replace(anchor, script + '\n' + anchor, 1) if anchor in s else s
    changed.append('脚本')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Allocations.vue 改动：', '、'.join(changed) if changed else '（无匹配）')
