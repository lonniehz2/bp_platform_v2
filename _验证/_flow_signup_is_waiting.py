# -*- coding: utf-8 -*-
"""报名即轮候（方案 A）落地：
1) 批次状态流转提示改为「报名即轮候」口径
2) 摇号前弹确认，显示本次将摇号的轮候人数与房源套数
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'views', 'Allocations.vue')

s = io.open(P, encoding='utf-8').read()

# 1) 提示语改为报名即轮候
old_tip = re.search(r'const TRANSITION_TIP = \{[\s\S]*?\}\n', s)
new_tip = '''const TRANSITION_TIP = {
  PUBLISHED: '发布后批次对外可见，可进入报名阶段',
  SIGNUP: '开始报名后，本批次按「报名即轮候」处理：该保障类型的轮候人员自动参与本批次摇号',
  LOTTERY: '结束报名并转入摇号，之后不可再报名；摇号对象为当前轮候池',
  CANCELLED: '取消后批次作废，已入池房源释放'
}

/** 轮候池人数（按保障类型统计，用于摇号前提示） */
async function waitingCountOf(securityType) {
  try {
    const d = await req.get('/allocation/waiting', { params: { pageNum: 1, pageSize: 1, securityType } })
    return Number((d && d.total) || 0)
  } catch (e) { return 0 }
}

/** 批次房源套数 */
async function batchHouseCount(batchId) {
  try {
    const d = await req.get(`/allocation/batches/${batchId}/houses`, { params: { pageNum: 1, pageSize: 1 } })
    return Number((d && d.total) || 0)
  } catch (e) { return 0 }
}
'''
if old_tip:
    s = s[:old_tip.start()] + new_tip + s[old_tip.end():]
    print('提示语已更新')

# 2) 摇号前确认
m = re.search(r'async function runLottery\(row\) \{[\s\S]*?\n\}', s)
if m and 'waitingCountOf' not in m.group(0):
    new_fn = '''async function runLottery(row) {
  const [waiting, houses] = await Promise.all([
    waitingCountOf(row.securityType),
    batchHouseCount(row.id)
  ])
  if (!waiting) {
    ElMessage.warning('当前轮候池中没有该保障类型的待配租人员，无法摇号')
    return
  }
  if (!houses) {
    ElMessage.warning('本批次还没有房源，请先「加房源」')
    return
  }
  try {
    await ElMessageBox.confirm(
      `本次将对 ${waiting} 名轮候人员与 ${houses} 套房源执行摇号（报名即轮候）。\\n`
      + '摇号结果生成后可在「结果」中查看，并用于公示。',
      '确认摇号',
      { type: 'warning', confirmButtonText: '开始摇号', cancelButtonText: '取消' })
  } catch (e) { return }
  try {
    await req.post('/allocation/lottery', { batchId: row.id, seed: seed.value || undefined })
    ElMessage.success('摇号完成')
    load()
    viewResults(row)
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '摇号失败')
  }
}'''
    s = s[:m.start()] + new_fn + s[m.end():]
    print('摇号确认已更新')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('完成')
