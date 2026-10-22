# -*- coding: utf-8 -*-
"""修掉批量脚本产生的 width="width="NNN"" 重复属性。"""
import glob
import io
import os
import re

V = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', 'src', 'views')
PAT = re.compile(r'width="width="(\d+)""')

fixed = 0
for p in sorted(glob.glob(os.path.join(V, '*.vue'))):
    s = io.open(p, encoding='utf-8').read()
    new = PAT.sub(lambda m: 'width="%s"' % m.group(1), s)
    if new != s:
        io.open(p, 'w', encoding='utf-8', newline='').write(new)
        print(os.path.basename(p), '已修')
        fixed += 1
print('合计修复 %d 个文件' % fixed)
