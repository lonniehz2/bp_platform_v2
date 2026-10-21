# -*- coding: utf-8 -*-
"""修正 MybatisTenantConfig 缺逗号导致的语法错误"""
import io

P = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\common\config\MybatisTenantConfig.java')
lines = io.open(P, encoding='utf-8').read().split('\n')

# 打印 38-52 以便确认
print('修正前：')
for i in range(37, min(53, len(lines))):
    print('  %d: %s' % (i + 1, lines[i]))

# 找到 "bp_open_api" 行，补逗号
for i, ln in enumerate(lines):
    if '"bp_open_api"' in ln and not ln.rstrip().endswith(','):
        lines[i] = ln.rstrip() + ','
        print('\n已在第 %d 行补逗号' % (i + 1))
        break

# 找到 bp_open_call_log 行，确保其后有逗号或正确结尾
for i, ln in enumerate(lines):
    if '"bp_open_call_log"' in ln:
        print('bp_open_call_log 在第 %d 行' % (i + 1))
        break

io.open(P, 'w', encoding='utf-8').write('\n'.join(lines))
