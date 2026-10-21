# -*- coding: utf-8 -*-
"""从 console.html 抽取每个功能区的表单字段与接口，生成 SPA 实现规格

输出：_console_spec.json + 控制台摘要
"""
import io
import json
import re
from collections import OrderedDict

P = r'D:\Work\业务平台开发\backend\src\main\resources\static\console.html'
OUT = r'D:\Work\业务平台开发\_验证\_console_spec.json'
s = io.open(P, encoding='utf-8').read()

# 以 h2/h3 + <section> 切块，最大化覆盖
blocks = re.split(r'(?=<h2|<h3|<section)', s)
spec = OrderedDict()

for blk in blocks:
    m = re.match(r'<h[23][^>]*>([^<]{2,60})</h[23]>', blk)
    if not m:
        continue
    title = re.sub(r'^[①②③④⑤⑥⑦⑧⑨⑩\s]+', '', m.group(1)).strip()
    # 该块内的 input/select/textarea 的 id 与 placeholder / label
    fields = []
    for mm in re.finditer(
            r'<(input|select|textarea)[^>]*?(?:id="([^"]+)")?[^>]*?'
            r'(?:placeholder="([^"]*)")?[^>]*?>', blk):
        fid = mm.group(2) or ''
        ph = mm.group(3) or ''
        if fid or ph:
            fields.append({'id': fid, 'placeholder': ph, 'tag': mm.group(1)})
    # 按钮文本（操作名）
    btns = [re.sub(r'\s+', '', b) for b in
            re.findall(r'<button[^>]*>([^<]{1,20})</button>', blk)]
    # 接口
    apis = list(OrderedDict.fromkeys(
        re.findall(r"['\"`](/api/v1/[^'\"`\s\)]+)['\"`]", blk)))
    if not apis and not fields:
        continue
    spec[title] = {
        'apis': [a.split('?')[0] for a in apis],
        'buttons': [b for b in btns if b][:12],
        'fields': [f for f in fields if f['id'] or f['placeholder']][:24],
    }

json.dump(spec, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

print('解析出 %d 个功能区\n' % len(spec))
for k, v in spec.items():
    print('■ %s' % k)
    print('   接口 %d：%s' % (len(v['apis']), ', '.join(a.replace('/api/v1', '')
                                                 for a in v['apis'][:5])))
    if len(v['apis']) > 5:
        print('          … 其余 %d' % (len(v['apis']) - 5))
    if v['buttons']:
        print('   按钮：%s' % ' / '.join(v['buttons'][:8]))
    if v['fields']:
        names = [f['id'] or f['placeholder'] for f in v['fields']][:10]
        print('   字段：%s' % ' / '.join(names))
    print()
print('规格已写入 %s' % OUT)
