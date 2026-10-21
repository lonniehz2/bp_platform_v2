# -*- coding: utf-8 -*-
"""清理 Spaces.vue 重复 import"""
import io

P = r'D:\Work\业务平台开发\frontend\src\views\Spaces.vue'
L = io.open(P, encoding='utf-8').read().split('\n')

out = []
seen_detail = False
for ln in L:
    t = ln.strip()
    if t == "import DetailView from '@/components/DetailView.vue'":
        if seen_detail:
            continue
        seen_detail = True
    # 与下行重复的 ElMessage 单独导入
    if t == "import { ElMessage } from 'element-plus'":
        continue
    out.append(ln)

s = '\n'.join(out)
io.open(P, 'w', encoding='utf-8').write(s)

print('剩余 import：')
for ln in s.split('\n'):
    if ln.strip().startswith('import '):
        print('  ' + ln.strip())
