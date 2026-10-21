# -*- coding: utf-8 -*-
"""处理多行 :title="HINT" 与 DetailView props"""
import io
import os
import re

V = r'D:\Work\业务平台开发\frontend\src\views'
HINTS = {
    'Cashflow': '核销/退款/补贴都会自动记账，形成完整资金流水',
    'ContractChanges': '调租/租期/承租人变更，批准后写回合同',
    'Publicities': '配租公示必须 ≥7 自然日且已结束才能签约',
    'Waitlist': '总分 = 优先附加分 + 轮候天数 × 0.1；摇号按总分降序',
}

for name, hint in HINTS.items():
    p = os.path.join(V, name + '.vue')
    s = io.open(p, encoding='utf-8').read()
    # 可能是多行形式：:title="HINT"\n  style=...
    if 'HINT' in s:
        s = s.replace(':title="HINT"', ":title=\"'%s'\"" % hint.replace("'", "\\'"))
        # 兜底：残留的 HINT 字符串
        s = re.sub(r'(?<![\w.])HINT(?![\w])',
                   "'%s'" % hint.replace("'", "\\'"), s)
        io.open(p, 'w', encoding='utf-8').write(s)
        print('  ✓ %-16s HINT → 文案' % name)

# DetailView：props 用对象字面量，把顶层键当声明（检查脚本已支持，但需确认写法）
P = r'D:\Work\业务平台开发\frontend\src\components\DetailView.vue'
s = io.open(P, encoding='utf-8').read()
print('\n  DetailView props 写法：')
for ln in s.split('\n'):
    if 'defineProps' in ln or 'type:' in ln or 'default:' in ln:
        print('    ' + ln.strip()[:90])
