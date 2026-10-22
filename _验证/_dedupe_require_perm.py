# -*- coding: utf-8 -*-
"""清理重复的 @RequirePerm 注解（同一方法上出现两条时保留第一条）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

PAT = re.compile(
    r'(\n\s*@com\.yundao\.bp\.iam\.security\.RequirePerm\("[^"]+"\)\n)'
    r'(\s*@com\.yundao\.bp\.iam\.security\.RequirePerm\("[^"]+"\)\n)')

total = 0
for dirpath, _, files in os.walk(JAVA):
    for fn in files:
        if not fn.endswith('.java'):
            continue
        p = os.path.join(dirpath, fn)
        s = io.open(p, encoding='utf-8').read()
        n = 0
        while True:
            m = PAT.search(s)
            if not m:
                break
            s = s[:m.start()] + m.group(1) + s[m.end():]
            n += 1
        if n:
            io.open(p, 'w', encoding='utf-8', newline='').write(s)
            print('%s：清理重复注解 %d 处' % (fn, n))
            total += n
print('合计清理 %d 处' % total)
