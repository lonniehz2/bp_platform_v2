# -*- coding: utf-8 -*-
import io

p = r'..\frontend\src\constants\fieldLabels.js'
lines = io.open(p, encoding='utf-8').read().splitlines()
lines = [l for l in lines if 'billingPersonCount' not in l and 'billingBedCount' not in l]
# 找到 FIELD_LABEL 对象结尾（workOrderType 后）
idx = next(i for i, l in enumerate(lines) if 'workOrderType:' in l)
lines[idx + 1:idx + 1] = ["  billingPersonCount: '计费人口',",
                          "  billingBedCount: '计费床位',"]
io.open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines) + '\n')
print('moved labels into FIELD_LABEL')
