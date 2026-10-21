# -*- coding: utf-8 -*-
"""把报表/大屏定义加入租户忽略表（它们支持「全局默认 + 租户覆盖」）"""
import io

p = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\common\config\MybatisTenantConfig.java')
s = io.open(p, encoding='utf-8').read()

if 'bp_rpt_report_def' not in s:
    anchor = '"bp_msg_template",      // 系统内置消息模板'
    assert anchor in s
    s = s.replace(anchor,
                  anchor + '\n'
                  '            "bp_rpt_report_def",    // 报表定义（全局默认 + 租户覆盖）\n'
                  '            "bp_rpt_screen_def",    // 大屏定义（全局默认 + 租户覆盖）', 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('  ✓ 报表/大屏定义已加入租户忽略表')
else:
    print('  - 已在忽略表')

# 打印当前忽略表清单，便于确认
import re
m = re.search(r'IGNORE_TABLES = Set\.of\((.*?)\);', s, re.S)
if m:
    names = re.findall(r'"(bp_[a-z_]+)"', m.group(1))
    print('  当前忽略表 %d 张：%s' % (len(names), ', '.join(names)))
