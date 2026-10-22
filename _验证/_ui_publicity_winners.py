# -*- coding: utf-8 -*-
"""公示页：新建时可关联配租批次；整行展开（或详情按钮）显示中签名单。

名单展示：姓名、身份证（脱敏）、手机（脱敏）、房号、摇号序号、结果。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Publicities.vue')

s = io.open(P, encoding='utf-8').read()

# 1) 展开行里加「中签名单」区块
expand = '''      <template #default="{ row }">
        <div style="padding:8px 12px">
          <div style="margin-bottom:6px">
            <strong>中签名单</strong>
            <span class="muted" style="margin-left:8px;font-size:12px">
              {{ winnersOf(row.id).length ? `共 ${winnersOf(row.id).length} 人` : '暂无中签记录（需先关联批次并完成摇号）' }}
            </span>
          </div>
          <el-table v-if="winnersOf(row.id).length" :data="winnersOf(row.id)"
                    size="small" border max-height="320">
            <el-table-column prop="lotterySeq" label="摇号序号" width="100" />
            <el-table-column prop="personName" label="姓名" width="110" />
            <el-table-column prop="idCardMask" label="身份证（脱敏）" width="190" />
            <el-table-column prop="phoneMask" label="手机（脱敏）" width="140" />
            <el-table-column prop="houseName" label="中签房源" min-width="170" />
            <el-table-column prop="selectSeq" label="选房序号" width="100" />
            <el-table-column prop="resultTypeLabel" label="结果" width="90">
              <template #default="{ row: w }">
                <el-tag size="small" :type="w.resultType === 'WIN' ? 'success' : 'info'">
                  {{ w.resultTypeLabel }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </template>'''

m = re.search(r'<el-table-column type="expand">\s*\n\s*<template #default="\{ row \}">[\s\S]*?</template>\s*\n\s*</el-table-column>', s)
if m and '中签名单' not in s:
    s = s[:m.start()] + '<el-table-column type="expand">\n' + expand + '\n    </el-table-column>' + s[m.end():]
    print('展开行已替换为中签名单')

# 2) 新建公示弹窗：加「关联批次」下拉（若已有创建弹窗）
if 'batchOptions' not in s:
    # 找表单里的 orgId 或第一个 el-form-item，插入批次选择
    m2 = re.search(r'(<el-form-item label="(?:标题|公示标题)[^"]*"[^>]*>[\s\S]{0,200}?</el-form-item>)', s)
    if m2:
        add = m2.group(1) + '''
        <el-form-item label="关联批次">
          <el-select v-model="cf.batchId" clearable filterable style="width:100%"
                     placeholder="可选：关联配租批次，用于展示中签名单">
            <el-option v-for="b in batchOptions" :key="b.id"
                       :label="`${b.batchName}（${b.batchNo || ''}）`" :value="String(b.id)" />
          </el-select>
        </el-form-item>'''
        s = s[:m2.start()] + add + s[m2.end():]
        print('新建弹窗已加关联批次')

# 3) 脚本：加载批次 + 中签名单缓存
script = '''
/** 中签名单：按公示 ID 缓存 */
const winnersMap = reactive({})
function winnersOf(publicityId) {
  if (!(publicityId in winnersMap)) {
    winnersMap[publicityId] = []
    req.get(`/publicities/${publicityId}/winners`).then((list) => {
      winnersMap[publicityId] = list || []
    }).catch(() => { winnersMap[publicityId] = [] })
  }
  return winnersMap[publicityId]
}

/** 可关联的配租批次 */
const batchOptions = ref([])
async function loadBatches() {
  if (batchOptions.value.length) return
  try {
    const d = await req.get('/allocation/batches', { params: { pageNum: 1, pageSize: 100 } })
    batchOptions.value = (d && d.rows) || []
  } catch (e) { batchOptions.value = [] }
}
'''
if 'function winnersOf' not in s:
    anchor = 'onMounted('
    i = s.find(anchor)
    s = s[:i] + script + '\n' + s[i:]
    print('脚本已加 winnersOf/loadBatches')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('Publicities.vue 处理完成')
