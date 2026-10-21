# -*- coding: utf-8 -*-
"""抽 console 每个功能区的接口调用（找真实 fetch 封装名）"""
import io
import re
from collections import OrderedDict

P = r'D:\Work\业务平台开发\backend\src\main\resources\static\console.html'
s = io.open(P, encoding='utf-8').read()

# 找自定义请求封装名
for name in ('bpFetch', 'apiGet', 'api(', 'callApi', 'request(', 'fetchJSON',
             'async function req', 'function api'):
    print('  %-16s 出现 %d 次' % (name, s.count(name)))

# 所有 /api/v1 字符串
paths = re.findall(r"['\"`](/api/v1/[^'\"`\s\)]+)['\"`]", s)
uniq = list(OrderedDict.fromkeys(paths))
print('\n接口字符串 %d 处，去重 %d 个' % (len(paths), len(uniq)))

# 按功能区切段：以 <h2/h3> 为界
parts = re.split(r'(<h[23][^>]*>[^<]*</h[23]>)', s)
print('\n=== 各功能区调用的接口 ===')
cur = None
bucket = OrderedDict()
for part in parts:
    m = re.match(r'<h[23][^>]*>([^<]*)</h[23]>', part)
    if m:
        cur = m.group(1).strip()
        bucket.setdefault(cur, [])
    elif cur:
        for pth in re.findall(r"['\"`](/api/v1/[^'\"`\s\)]+)['\"`]", part):
            if pth.split('?')[0] not in bucket[cur]:
                bucket[cur].append(pth.split('?')[0])

for k, v in bucket.items():
    if not v:
        continue
    print('  %-28s %2d 个接口' % (k[:28], len(v)))
    for p in v[:6]:
        print('       ' + p)
    if len(v) > 6:
        print('       … 其余 %d 个' % (len(v) - 6))
