# -*- coding: utf-8 -*-
"""同步忽略清单测试：加入 bp_open_call_log 及理由"""
import io
import re

P = r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\iam\IamModuleTest.java'
s = io.open(P, encoding='utf-8').read()

# 1) 注释补理由
if 'bp_open_call_log' not in s:
    anchor = re.search(r'(//\s*bp_rpt_screen_def[^\n]*\n)', s)
    if anchor:
        s = s[:anchor.end()] + (
            '        //   bp_open_call_log      开放平台调用日志，按 appKey 归属，表无 tenant_id 列\n'
            '        //                         （不忽略会导致租户插件给 INSERT 注入 tenant_id 而写入失败）\n'
        ) + s[anchor.end():]

# 2) 期望集合补元素
m = re.search(r'Set\.of\(([^)]*)\)', s[s.find('ignoreTablesMinimal'):])
if m:
    seg_start = s.find('ignoreTablesMinimal') + m.start()
    args = m.group(1)
    if 'bp_open_call_log' not in args:
        new_args = args.rstrip().rstrip(',') + ', "bp_open_call_log"'
        s = s[:seg_start] + 'Set.of(' + new_args + ')' + s[seg_start + m.end():]

io.open(P, 'w', encoding='utf-8').write(s)

# 校验
i = s.find('ignoreTablesMinimal')
seg = s[i:i + 2600]
mm = re.search(r'Set\.of\(([^)]*)\)', seg)
print('期望集合：')
print('  ' + re.sub(r'\s+', ' ', mm.group(1)) if mm else '  未找到')
