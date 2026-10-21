# -*- coding: utf-8 -*-
"""补齐来访走访核查字段与缺失枚举"""
import io
import re

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 字段中文名 ----------
P = FE + r'\constants\fieldLabels.js'
s = io.open(P, encoding='utf-8').read()
NEW = {
    'idle': '是否空置',
    'illegalUse': '是否违规使用',
    'occupied': '是否有人居住',
    'sublease': '是否转租',
    'visitType': '走访类型',
    'visitDate': '走访日期',
    'visitResult': '走访结果',
    'visitorName': '走访人',
}
add = [(k, v) for k, v in NEW.items()
       if not re.search(r"^\s{2}%s:\s*'" % k, s, re.M)]
if add:
    block = '\n  // ---------- 走访/核查（实测补充） ----------\n'
    for k, v in add:
        block += "  %s: '%s',\n" % (k, v)
    s = s.replace('export const FIELD_LABEL = {',
                  'export const FIELD_LABEL = {' + block, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ 补字段中文名 %d 个' % len(add))

# ---------- 2) 枚举 ----------
E = FE + r'\constants\enums.js'
e = io.open(E, encoding='utf-8').read()
ENUMS = {
    'ROUTINE': '常规走访', 'VERIFY': '资格核查', 'VACANCY': '空置核查',
    'ALERT': '预警核查',
    'UNRECONCILED': '未对账', 'RECONCILING': '对账中', 'DIFF': '有差异',
}
add2 = [(k, v) for k, v in ENUMS.items()
        if not re.search(r"^\s*'?%s'?\s*:" % k, e, re.M)]
if add2:
    block = '\n  // ---------- 走访/对账（实测补充） ----------\n'
    for k, v in add2:
        block += "  %s: '%s',\n" % (k, v)
    e = e.replace('  // ---------- 房源 / 空间 ----------',
                  block + '\n  // ---------- 房源 / 空间 ----------', 1)
    io.open(E, 'w', encoding='utf-8').write(e)
    print('  ✓ 补枚举 %d 个：%s' % (len(add2), ', '.join(k for k, _ in add2)))

# ---------- 3) 后端 EnumLabels 同步 ----------
J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp\common\util\EnumLabels.java'
j = io.open(J, encoding='utf-8').read()
add3 = []
for k, v in {**ENUMS}.items():
    if '"%s"' % k not in j:
        add3.append('            new String[]{"%s", "%s"}' % (k, v))
if add3:
    j = j.replace('        );\n        for (String[] p : pairs) {',
                  ',\n'.join(add3) + '\n        );\n        for (String[] p : pairs) {', 1)
    # 修掉前一行缺逗号
    j = re.sub(r'(\{"([^"]+)", "([^"]+)"\})\n(\s+new String\[\])', r'\1,\n\4', j)
    io.open(J, 'w', encoding='utf-8').write(j)
    print('  ✓ 后端 EnumLabels 补 %d 条' % len(add3))
