# -*- coding: utf-8 -*-
"""剩余金额列统一 $money。"""
import io
import os
import re

V = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'views'))
TARGETS = {
    'Arrears.vue': ['payableAmount'],
    'Bills.vue': ['amount', 'unitPrice'],
    'Cashflow.vue': ['systemAmount', 'channelAmount', 'payAmount', 'remainAmount'],
    'ShortRent.vue': ['totalAmount'],
    'Subsidies.vue': ['subsidyValue', 'maxAmount'],
    'Terminations.vue': ['depositAmount'],
}

for fn, props in TARGETS.items():
    p = os.path.join(V, fn)
    s = io.open(p, encoding='utf-8').read()
    n = 0
    for prop in set(props):
        pat = re.compile(r'<el-table-column prop="%s"([^>]*?)/>' % re.escape(prop))

        def repl(m):
            global n
            n += 1
            return ('<el-table-column%s>\n'
                    '          <template #default="{ row }">{{ $money(row.%s) }}</template>\n'
                    '        </el-table-column>' % (m.group(1), prop))
        s = pat.sub(repl, s)
    if n:
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        print(fn, n)
