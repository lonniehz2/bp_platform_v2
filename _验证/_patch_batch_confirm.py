# -*- coding: utf-8 -*-
"""批量/资金类操作加二次确认。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
V = os.path.join(ROOT, 'frontend', 'src', 'views')


def patch(fn, old, new, label, imp=False):
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    if old not in s:
        print('  !', fn, '未匹配:', label)
        return
    s = s.replace(old, new, 1)
    if imp and 'ElMessageBox' not in s:
        s = s.replace("import { ElMessage } from 'element-plus'",
                      "import { ElMessage, ElMessageBox } from 'element-plus'", 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('  ✔', fn, label)


# 在参数校验后插入确认
patch('Bills.vue', '''  if (g.periodEnd <= g.periodStart) { ElMessage.warning('费用截止日必须晚于起始日'); return }
  saving.value = true''', '''  if (g.periodEnd <= g.periodStart) { ElMessage.warning('费用截止日必须晚于起始日'); return }
  if (!g.dryRun) {
    await ElMessageBox.confirm(
      '将为该组织/项目/费用区间内符合条件的合同生成账单；已出过账的会自动跳过。是否继续？',
      '确认批量出账', { type: 'warning' })
  }
  saving.value = true''', '批量出账确认')

patch('Bills.vue', '''async function batchDunning() {
  const picked = selected.value
  if (!picked.length) { ElMessage.warning('请先勾选账单'); return }''',
      '''async function batchDunning() {
  const picked = selected.value
  if (!picked.length) { ElMessage.warning('请先勾选账单'); return }
  await ElMessageBox.confirm('将向已选 ' + picked.length + ' 张账单发起催缴，是否继续？',
    '确认批量催缴', { type: 'warning' })''', '批量催缴确认')

patch('MeterReadings.vue', '''  if (!ids.length) { ElMessage.warning('请勾选未出账的记录'); return }''',
      '''  if (!ids.length) { ElMessage.warning('请勾选未出账的记录'); return }
  await ElMessageBox.confirm('将为已选 ' + ids.length + ' 条读数生成账单，是否继续？',
    '确认批量出账', { type: 'warning' })''', '抄表批量出账确认', imp=True)

patch('Subsidies.vue', '''async function doBatch() {
  if (!bf.subsidyPeriod) { ElMessage.warning('请填写补贴周期'); return }
  saving.value = true''',
      '''async function doBatch() {
  if (!bf.subsidyPeriod) { ElMessage.warning('请填写补贴周期'); return }
  await ElMessageBox.confirm('将按所选标准批量发放补贴，涉及资金，是否继续？',
    '确认批量发放', { type: 'warning' })
  saving.value = true''', '批量发放确认')

patch('AnnualReviews.vue', '''async function doBatch() {
  saving.value = true''',
      '''async function doBatch() {
  await ElMessageBox.confirm('将为符合条件的人员批量发起年审，是否继续？',
    '确认批量年审', { type: 'warning' })
  saving.value = true''', '批量年审确认')

patch('WorkOrders.vue', '''async function autoAssignPending() {
  saving.value = true''',
      '''async function autoAssignPending() {
  await ElMessageBox.confirm('将为所有待派单工单自动分配责任人，是否继续？',
    '确认批量派单', { type: 'warning' })
  saving.value = true''', '批量派单确认')
