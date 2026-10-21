# -*- coding: utf-8 -*-
"""导出 P0 非 record 接口的参数签名（@RequestParam / @RequestBody Map）"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
KEY = re.compile(r'/(sign|renew|terminate|generate|generate-batch|waive|cancel|'
                 r'allocate|lottery|give-up|review|batch|scan|close|publish|'
                 r'dunning|recalc|release-expired|confirm|complete|receive|deduct)',
                 re.I)

rows = []
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        base = bm.group(1) if bm else ''
        # 方法块：注解 + 方法签名
        for mm in re.finditer(
                r'(@(?:Get|Post|Put|Delete)Mapping'
                r'(?:\s*\(\s*(?:value\s*=\s*)?"([^"]*)"?\s*\))?)'
                r'[\s\S]{0,400}?public\s+[\w<>,\s\.\[\]]+\s+(\w+)\s*\(([^)]*)\)', s):
            sub = mm.group(2) or ''
            full = base + ('/' + sub if sub else '')
            if not KEY.search(full):
                continue
            params = re.sub(r'@[\w.]+(\([^)]*\))?', '', mm.group(4))
            params = re.sub(r'\s+', ' ', params).strip()
            # 保留原始参数串（含注解）以便看 @RequestParam 名
            raw = re.sub(r'\s+', ' ', mm.group(4)).strip()
            rows.append((full, mm.group(1).split('(')[0], mm.group(3), raw))

seen = set()
print('P0 写操作接口参数（%d 个）\n' % len(rows))
for full, ann, meth, raw in sorted(set(rows)):
    if full in seen:
        continue
    seen.add(full)
    print('■ %-46s %s' % (full, ann.replace('@', '')))
    # 提取参数名与类型
    for p in re.split(r',\s*(?=@|\w+\s+\w+$)', raw):
        p = p.strip()
        if not p:
            continue
        print('     ' + p[:110])
    print()
