# -*- coding: utf-8 -*-
"""列出 PublicityReviewController 每个接口：路径、推导权限码、是否已注解。"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _perm_rules import derive

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', 'src',
                 'main', 'java', 'com', 'yundao', 'bp', 'biz', 'controller',
                 'PublicityReviewController.java')
lines = io.open(P, encoding='utf-8').read().splitlines()
base = '/api/v1'
print('%-6s %-24s %-38s %-26s %s' % ('方法', '方法名', '路径', '推导权限码', '注解'))
for i, line in enumerate(lines):
    m = re.search(r'@(Get|Post|Put|Delete)Mapping(?:\("([^"]*)"\))?', line)
    if not m:
        continue
    kind, sub = m.group(1), (m.group(2) or '')
    name = ''
    for f in range(i, min(len(lines), i + 6)):
        m2 = re.search(r'public\s+[\w<>,\s\.\[\]]+?\s(\w+)\(', lines[f])
        if m2:
            name = m2.group(1)
            break
    has = False
    for b in range(i - 1, max(-1, i - 12), -1):
        if 'RequirePerm' in lines[b]:
            has = True
            break
        if ('Mapping' in lines[b] and '@' in lines[b]) or 'class ' in lines[b] \
                or lines[b].strip().startswith('}') or 'public ' in lines[b]:
            break
    for f in range(i + 1, min(len(lines), i + 6)):
        if 'RequirePerm' in lines[f]:
            has = True
            break
        if 'public ' in lines[f]:
            break
    d = derive(base, kind, sub)
    print('%-6s %-24s %-38s %-26s %s' % (kind, name, sub, (d[0] if d else 'None'),
                                         '有' if has else '缺'))
