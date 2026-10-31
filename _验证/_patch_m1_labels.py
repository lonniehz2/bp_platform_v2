# -*- coding: utf-8 -*-
import io

p = r'..\frontend\src\constants\fieldLabels.js'
s = io.open(p, encoding='utf-8').read()
if 'billingPersonCount' not in s:
    i = s.rfind('}')
    s = s[:i] + "  billingPersonCount: '计费人口',\n  billingBedCount: '计费床位',\n" + s[i:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('labels added')
else:
    print('already exists')
