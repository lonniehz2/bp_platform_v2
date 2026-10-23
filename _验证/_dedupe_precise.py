# -*- coding: utf-8 -*-
"""精确去重 v2：同一方法（映射注解前后）若有多条 RequirePerm，只保留最靠近方法签名的一条。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')

total_removed = 0
for dirpath, _, files in os.walk(JAVA):
    for fn in files:
        if not fn.endswith('Controller.java'):
            continue
        p = os.path.join(dirpath, fn)
        lines = io.open(p, encoding='utf-8').read().splitlines(True)
        drop = set()
        for i, line in enumerate(lines):
            if not re.search(r'@(Get|Post|Put|Delete)Mapping', line):
                continue
            # 向上：直到上一个 Mapping / 方法边界
            start = i - 1
            while start >= 0:
                prev = lines[start].strip()
                if ('Mapping' in prev and prev.startswith('@')) or prev.startswith('class ') \
                        or prev.startswith('public ') or prev.startswith('private ') \
                        or prev.startswith('protected ') or prev.startswith('}'):
                    break
                start -= 1
            # 向下：直到方法签名
            end = i + 1
            while end < len(lines):
                nxt = lines[end].strip()
                if nxt.startswith('public ') or nxt.startswith('private ') \
                        or nxt.startswith('protected '):
                    break
                end += 1
            block = list(range(start + 1, i)) + list(range(i + 1, end))
            perm_lines = [k for k in block if 'RequirePerm' in lines[k]]
            if len(perm_lines) > 1:
                # 保留距签名最近的一条（即最大索引）
                keep = max(perm_lines)
                for k in perm_lines:
                    if k != keep:
                        drop.add(k)
        if drop:
            out = [ln for k, ln in enumerate(lines) if k not in drop]
            io.open(p, 'w', encoding='utf-8', newline='').write(''.join(out))
            print('%s：移除重复注解 %d 处' % (fn, len(drop)))
            total_removed += len(drop)

print('合计移除 %d 处' % total_removed)
