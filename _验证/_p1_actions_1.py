# -*- coding: utf-8 -*-
"""P1 接线（第一批）：投诉处理/评价/转工单、公示发布、轮候退出。

只加按钮 + 动作函数，字段按后端 DTO：
  POST /complaints/{id}/resolve        {handleUserId, action, result}
  POST /complaints/{id}/evaluate       {satisfaction}
  POST /complaints/{id}/to-workorder   {handleUserId, action}
  POST /publicities/{id}/publish       (无 body)
  POST /allocation/waiting/{id}/exit   {reason}
"""
import io
import os

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')

# ---------------- 投诉 ----------------
p = os.path.join(V, 'Complaints.vue')
s = io.open(p, encoding='utf-8').read()
OLD_BTN = """          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/complaints/{id}/close', '办结')">办结</el-button>"""
NEW_BTN = """          <el-button link type="primary" @click="openDetail(row)" data-testid="row-detail">详情</el-button>
          <el-button link type="primary" @click="doResolve(row)">处理</el-button>
          <el-button link type="warning" @click="doEvaluate(row)">评价</el-button>
          <el-button link type="success" @click="doToWorkOrder(row)">转工单</el-button>
          <el-button link type="primary" @click="actReason(row, '/api/v1/complaints/{id}/close', '办结')">办结</el-button>"""
if OLD_BTN in s and 'doResolve' not in s:
    s = s.replace(OLD_BTN, NEW_BTN, 1)
    s = s.replace('<el-table-column label="操作" width="210" fixed="right">',
                  '<el-table-column label="操作" width="360" fixed="right">', 1)
    FUNCS = """/** 处理：记录处理结果 */
async function doResolve(row) {
  const { value } = await ElMessageBox.prompt('处理结果（可空）', '处理投诉',
    { inputValue: '已联系投诉人并处理' })
  await req.post(`/complaints/${row.id}/resolve`, {
    handleUserId: 1, action: '处理', result: value || '已处理'
  })
  ElMessage.success('已处理'); load()
}

/** 评价：满意度 1-5 */
async function doEvaluate(row) {
  const { value } = await ElMessageBox.prompt('满意度评分（1-5）', '投诉评价',
    { inputValue: '5', inputValidator: (v) => (/^[1-5]$/.test(String(v).trim())
      ? true : '请输入 1-5 的整数') })
  await req.post(`/complaints/${row.id}/evaluate`,
    { satisfaction: Number(String(value).trim()) })
  ElMessage.success('评价已记录'); load()
}

/** 转工单：生成维修/服务工单 */
async function doToWorkOrder(row) {
  await ElMessageBox.confirm('确认将该投诉转为工单处理？', '转工单', { type: 'warning' })
  await req.post(`/complaints/${row.id}/to-workorder`,
    { handleUserId: 1, action: '转工单' })
  ElMessage.success('已转工单'); load()
}

/** 带原因的动作 */"""
    s = s.replace('/** 带原因的动作 */', FUNCS, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('投诉页已加 处理/评价/转工单')
else:
    print('投诉页跳过（已存在或锚点不符）')

# ---------------- 公示 ----------------
p = os.path.join(V, 'Publicities.vue')
s = io.open(p, encoding='utf-8').read()
OLD = """      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>"""
NEW = """      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :disabled="row.publicityStatus === 'PUBLISHED'"
                     @click="doPublish(row)">发布</el-button>
          <el-button link @click="detail = row; show = true">详情</el-button>
        </template>
      </el-table-column>"""
if OLD in s and 'doPublish' not in s:
    s = s.replace(OLD, NEW, 1)
    s = s.replace("import { ElMessage } from 'element-plus'",
                  "import { ElMessage, ElMessageBox } from 'element-plus'", 1)
    s = s.replace('</script>', """/** 发布公示（发布后对外可见，进入公示期） */
async function doPublish(row) {
  await ElMessageBox.confirm(
    `确认发布「${row.publicityTitle || row.publicityNo}」？发布后进入公示期。`,
    '发布公示', { type: 'warning' })
  await req.post(`/publicities/${row.id}/publish`)
  ElMessage.success('已发布'); load()
}
</script>""", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('公示页已加发布')
else:
    print('公示页跳过')
