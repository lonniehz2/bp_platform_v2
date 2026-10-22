# -*- coding: utf-8 -*-
"""移除脚本自动加的、与既有注解重复的 @RequirePerm。

判定：同一方法（@GetMapping 等映射行之后紧邻）出现两条 @RequirePerm，
删除 FULLY-QUALIFIED 的那条（脚本加的），保留原有的简短注解。
"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

FQ = re.compile(r'\n\s*@com\.yundao\.bp\.iam\.security\.RequirePerm\("[^"]+"\)(?=\s*\n)')

total = 0
for dirpath, _, files in os.walk(JAVA):
    for fn in files:
        if not fn.endswith('Controller.java'):
            continue
        p = os.path.join(dirpath, fn)
        s = io.open(p, encoding='utf-8').read()
        lines = s.splitlines(True)
        out = []
        removed = 0
        i = 0
        while i < len(lines):
            line = lines[i]
            if '@com.yundao.bp.iam.security.RequirePerm' in line:
                # 前后 6 行内是否已有普通 @RequirePerm
                ctx = ''.join(lines[max(0, i - 6):i] + lines[i + 1:i + 7])
                if re.search(r'@RequirePerm\(', ctx):
                    removed += 1
                    i += 1
                    continue
            out.append(line)
            i += 1
        if removed:
            io.open(p, 'w', encoding='utf-8', newline='').write(''.join(out))
            print('%s：移除重复注解 %d 处' % (fn, removed))
            total += removed
print('合计 %d 处' % total)
