# -*- coding: utf-8 -*-
"""配租批次：补「发布」「开始报名」「转摇号」「取消」入口（状态流转按钮）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Allocations.vue')

s = io.open(P, encoding='utf-8').read()

# 1) 行内按钮
if 'doTransition' not in s:
    m = re.search(r'(<el-button link type="primary" @click="openAddHouses\(row\)"[^>]*>加房源</el-button>)', s)
    if m:
        extra = m.group(1) + '''
            <el-button v-if="row.batchStatus === 'DRAFT'" link type="success"
                       @click="doTransition(row, 'PUBLISHED')"
                       data-testid="batch-publish">发布</el-button>
            <el-button v-if="row.batchStatus === 'PUBLISHED'" link type="primary"
                       @click="doTransition(row, 'SIGNUP')"
                       data-testid="batch-signup">开始报名</el-button>
            <el-button v-if="row.batchStatus === 'SIGNUP'" link type="warning"
                       @click="doTransition(row, 'LOTTERY')"
                       data-testid="batch-to-lottery">结束报名</el-button>
            <el-button v-if="['DRAFT','PUBLISHED','SIGNUP'].includes(row.batchStatus)"
                       link type="danger" @click="doTransition(row, 'CANCELLED')">取消</el-button>'''
        s = s[:m.start()] + extra + s[m.end():]
        print('行内按钮已加')

    script = '''
/** 批次状态流转：发布 → 报名 → 摇号 */
const TRANSITION_TIP = {
  PUBLISHED: '发布后批次对外可见，可开始报名',
  SIGNUP: '开始报名后，符合条件的申请人进入本批次',
  LOTTERY: '结束报名并转入摇号，之后不可再报名',
  CANCELLED: '取消后批次作废，已入池房源释放'
}
async function doTransition(row, target) {
  try {
    await ElMessageBox.confirm(TRANSITION_TIP[target] || '确认变更状态？', '状态变更',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' })
  } catch (e) { return }
  try {
    await req.post(`/allocation/batches/${row.id}/status`, { batchStatus: target })
    ElMessage.success('状态已更新')
    load()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '状态变更失败')
  }
}
'''
    anchor = 'onMounted(load)'
    s = s.replace(anchor, script + '\n' + anchor, 1) if anchor in s else s
    print('脚本已加 doTransition')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('完成')
