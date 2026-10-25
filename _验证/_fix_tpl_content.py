# -*- coding: utf-8 -*-
"""修正旅程13 模板内容中的 ${var} 占位（避免 shell 转义丢失）。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_check_journeys_edge.py')
s = io.open(P, encoding='utf-8').read()

DOLLAR = chr(36)
TPL = "尊敬的" + DOLLAR + "{name}，您本期应缴 " + DOLLAR + "{amount} 元，请及时缴纳。"

# 找到 contentTpl 行并整行替换
lines = s.split('\n')
for i, ln in enumerate(lines):
    if "'contentTpl'" in ln:
        indent = ln[:len(ln) - len(ln.lstrip())]
        lines[i] = indent + "'contentTpl': " + repr(TPL) + ","
        print('已替换第', i + 1, '行')
s = '\n'.join(lines)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('模板内容:', TPL)
