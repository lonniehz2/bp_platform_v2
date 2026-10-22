# -*- coding: utf-8 -*-
"""修正 _add_require_perm.py 的路径解析与已有注解检测。"""
import io
import os
import re

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_add_require_perm.py')
s = io.open(P, encoding='utf-8').read()

# 1) 替换 module_of / resource_of 为基于语义段的实现
old_mod = s[s.index('def module_of(path):'):s.index('def main():')]
new_mod = '''def segs(path):
    """拆出语义段：跳过 /api/v1 与 {param} 段"""
    parts = [p for p in path.split('/') if p]
    if parts and parts[0] == 'api':
        parts = parts[2:]
    return [p for p in parts if not p.startswith('{')]


def module_of(path):
    ss = segs(path)
    return ss[0] if ss else ''


def resource_of(path):
    ss = segs(path)
    seg = ss[1] if len(ss) > 1 else (ss[0] if ss else '')
    return RES_ALIAS.get(seg, seg)


'''
s = s.replace(old_mod, new_mod, 1)

# 2) 已有注解向前看 8 行
s = s.replace("ctx = ''.join(lines[max(0, i - 3):i])", "ctx = ''.join(lines[max(0, i - 8):i])")

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已修正 module_of/resource_of 与注解检测窗口')
