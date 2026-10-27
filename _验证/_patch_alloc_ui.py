# -*- coding: utf-8 -*-
"""配租页：批次联动配租单、人员列、生成提示、结果人员列。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VIEWS = os.path.join(ROOT, 'frontend', 'src', 'views')

p = os.path.join(VIEWS, 'Allocations.vue')
s = io.open(p, encoding='utf-8').read()


def rep(old, new, count=1):
    global s
    if old not in s:
        print('未匹配:', old[:50].replace('\n', ' '))
        return
    s = s.replace(old, new, count)


# 1) 批次表：行点击联动 + 高亮
rep('''      <el-table :data="batches" v-loading="loading" border size="small">''',
    '''      <el-table :data="batches" v-loading="loading" border size="small"
                highlight-current-row @row-click="(row) => selectBatch(row)">''')

# 2) 配租单标题：当前批次 + 全部
rep('''      <h3 style="margin:0 0 12px">配租单</h3>''',
    '''      <div class="toolbar" style="margin-bottom:12px">
        <h3 style="margin:0">配租单</h3>
        <span class="muted" v-if="currentBatch">
          当前批次：{{ currentBatch.batchNo }} {{ currentBatch.batchName }}
        </span>
        <div class="spacer" />
        <el-button v-if="currentBatch" @click="clearBatch">显示全部配租单</el-button>
      </div>''')

# 3) 配租单列：姓名/手机
rep('''        <el-table-column prop="personId" label="人员" width="110">
          <template #default="{ row }">{{ row.personName || row.personId }}</template>
        </el-table-column>''',
    '''        <el-table-column prop="personId" label="人员" width="150">
          <template #default="{ row }">{{ row.personName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="phoneMask" label="手机号" width="130" />''')

# 4) 结果表：姓名/手机
rep('''        <el-table-column prop="personId" label="人员" width="120">
          <template #default="{ row }">{{ row.personName || row.personId }}</template>
        </el-table-column>''',
    '''        <el-table-column prop="personId" label="人员" width="150">
          <template #default="{ row }">{{ row.personName || row.personId }}</template>
        </el-table-column>
        <el-table-column prop="phoneMask" label="手机号" width="130" />''')

# 5) 状态：当前批次
rep('''const batches = ref([])''',
    '''const batches = ref([])
const currentBatch = ref(null)''')

# 6) load 拆分：批次列表 + 配租单（可按批次）
rep('''    batches.value = b.rows || []
    const a = await allocationApi.allocations({ pageNum: 1, pageSize: 50 })
    allocations.value = a.rows || []''',
    '''    batches.value = b.rows || []
    await loadAllocations()''')

rep('''async function load() {''',
    '''/** 配租单：默认全部，选中批次后按批次过滤 */
async function loadAllocations() {
  const a = await allocationApi.allocations({
    pageNum: 1, pageSize: 100,
    batchId: currentBatch.value ? currentBatch.value.id : undefined
  })
  allocations.value = a.rows || []
}

function selectBatch(row) {
  currentBatch.value = row
  loadAllocations()
}

function clearBatch() {
  currentBatch.value = null
  loadAllocations()
}

async function load() {''')

# 7) 生成配租单提示
rep('''    const n = await req.post('/allocation/batches/' + row.id + '/generate-allocations')
    ElMessage.success('已生成配租单 ' + (n || 0) + ' 张，可在下方「配租单」查看')
    load()''',
    '''    const r = await req.post('/allocation/batches/' + row.id + '/generate-allocations')
    ElMessage.success(r?.message || ('本次生成 ' + (r?.generated || 0) + ' 张配租单'))
    currentBatch.value = row
    await loadAllocations(); load()''')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('Allocations.vue 已更新')
