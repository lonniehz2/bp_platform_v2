# -*- coding: utf-8 -*-
"""扫描前端：req.xxx( 后面直接跟 / 的坏路径（曾因模板字符串被吃掉）。"""
import io
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src')
pat = re.compile(r"req\.(get|post|put|delete)\(\s*/(?![`'\"])")
bad = []
for dirpath, _d, files in os.walk(ROOT):
    for f in files:
        if not f.endswith(('.vue', '.js')):
            continue
        p = os.path.join(dirpath, f)
        s = io.open(p, encoding='utf-8', errors='replace').read()
        for m in pat.finditer(s):
            line = s[:m.start()].count('\n') + 1
            frag = s[m.start():m.start() + 60].replace('\n', ' ')
            bad.append((os.path.relpath(p, ROOT), line, frag))
print('坏调用: %d' % len(bad))
for rel, line, frag in bad:
    print('  %s:%d  %s' % (rel, line, frag))
