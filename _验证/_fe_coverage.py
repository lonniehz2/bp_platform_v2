# -*- coding: utf-8 -*-
"""前端覆盖度盘点：后端接口 vs 前端页面/API 封装"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 后端：按 Controller 统计 ----------
backend = []
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        p = os.path.join(root, f)
        s = io.open(p, encoding='utf-8').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        base = m.group(1) if m else '?'
        cnt = len(re.findall(r'@(Get|Post|Put|Delete)Mapping', s))
        backend.append((f.replace('Controller.java', ''), base, cnt))
backend.sort(key=lambda x: -x[2])

# ---------- 前端：收集所有请求路径 ----------
fe_text = []
for root, _, files in os.walk(FE):
    for f in files:
        if f.endswith(('.js', '.vue')):
            fe_text.append(io.open(os.path.join(root, f), encoding='utf-8').read())
fe_all = '\n'.join(fe_text)

# 前端出现的 /api 路径片段（含模板串）
fe_paths = set(re.findall(r"'(/[a-z0-9\-/{}$\.]+)'", fe_all))
fe_paths |= set(re.findall(r'`(/[a-z0-9\-/{}$\.]+)`', fe_all))
fe_raw = ' '.join(sorted(fe_paths))

pages = sorted(x.replace('.vue', '') for x in os.listdir(os.path.join(FE, 'views')))
h5 = sorted(x.replace('.vue', '') for x in os.listdir(os.path.join(FE, 'h5', 'views')))

print('=' * 78)
print(' 后端 %d 个 Controller / %d 个接口' % (len(backend), sum(b[2] for b in backend)))
print(' 前端 %d 个 PC 页面 / %d 个 H5 页面' % (len(pages), len(h5)))
print('=' * 78)
print()
print('%-30s %-32s %5s  %s' % ('Controller', '根路径', '接口', '前端是否调用'))
print('-' * 78)
missing = []
for name, base, cnt in backend:
    # 用根路径的关键片段判断前端是否调用
    key = base.replace('/api/v1/', '').split('/')[0]
    hit = ('/' + key) in fe_raw
    mark = '✓' if hit else '✗ 未覆盖'
    print('%-30s %-32s %5d  %s' % (name[:30], base[:32], cnt, mark))
    if not hit:
        missing.append((name, base, cnt))

print()
print('=' * 78)
print(' 未被前端调用的模块：%d 个 / 共 %d 个 Controller' % (len(missing), len(backend)))
print(' 涉及接口数：%d / %d' % (sum(m[2] for m in missing), sum(b[2] for b in backend)))
print('=' * 78)
for name, base, cnt in sorted(missing, key=lambda x: -x[2]):
    print('  %-30s %-34s %3d 个接口' % (name[:30], base[:34], cnt))
