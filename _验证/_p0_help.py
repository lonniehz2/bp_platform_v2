# -*- coding: utf-8 -*-
"""帮助文案对齐 P0：催缴双页签、告警处理、退租与工单动作。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()

OLD_ARR = """      { type: 'h3', text: '6.5 催缴管理' },
      {
        type: 'ol', items: [
          '「扫描生成催缴」按逾期天数批量生成催缴动作。',
          '也可手工「登记催缴」（短信/微信/电话/上门/书面）。',
          '对拒不缴纳的可执行欠费停权（默认只停门锁、不停大门）。',
          '页面顶部两张图展示逾期金额与逾期账单数趋势。'
        ]
      },"""

NEW_ARR = """      { type: 'h3', text: '6.5 催缴管理（欠费处置 / 催缴通知）' },
      {
        type: 'ol', items: [
          '「欠费处置」是主线：扫描逾期合同 → 生成处置 → 执行 → 撤销，全程留痕。',
          '处置动作：通知催缴 / 冻结权限 / 解冻 / 限制续租 / 到期不续 / 司法程序。',
          '冻结权限会联动通行授权；默认只停门锁、不停大门（EXCLUDE_MAIN_DOOR），停大门需勾选安全风险。',
          '「催缴通知」用于查看已发出的短信/微信/电话/上门/书面记录，也可手工登记。',
          '页面顶部两张图展示逾期金额与逾期账单数趋势。'
        ]
      },"""

OLD_ALERT = """      { type: 'h3', text: '8.2 告警与规则' },"""
NEW_ALERT = """      { type: 'h3', text: '8.2 告警处理' },"""

n = 0
if OLD_ARR in s:
    s = s.replace(OLD_ARR, NEW_ARR, 1)
    n += 1
if OLD_ALERT in s:
    s = s.replace(OLD_ALERT, NEW_ALERT, 1)
    n += 1

# 告警段落描述：补「升级」
s = s.replace("对触发告警进行「处理", "对触发告警进行「处理")
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助段落更新:', n)
