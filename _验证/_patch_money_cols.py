# -*- coding: utf-8 -*-
"""金额列统一千分位：把常见金额 prop 列替换为 $money 模板。"""
import io
import os
import re

V = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'views'))
TARGETS = {
    'Bills.vue': ['billAmount', 'paidAmount', 'waivedAmount', 'payableAmount', 'lateFee'],
    'Deposits.vue': ['depositAmount', 'paidAmount', 'deductAmount', 'refundAmount',
                     'balanceAmount', 'refundAmount', 'amount'],
    'Subsidies.vue': ['subsidyAmount'],
    'Arrears.vue': ['arrearsAmount'],
    'Contracts.vue': ['monthlyRent', 'depositAmount', 'actualPay', 'subsidyAmount',
                      'rentPrice'],
    'FeeItems.vue': ['unitPrice'],
    'MeterReadings.vue': ['amount'],
    'EnergyAnalysis.vue': ['amount', 'cost', 'totalAmount'],
}

for fn, props in TARGETS.items():
    p = os.path.join(V, fn)
    if not os.path.exists(p):
        print('  ! 缺文件', fn)
        continue
    s = io.open(p, encoding='utf-8').read()
    n = 0
    for prop in set(props):
        pat = re.compile(
            r'<el-table-column prop="%s"([^>]*?)/>' % re.escape(prop))
        def repl(m):
            global n
            n += 1
            return ('<el-table-column%s>\n'
                    '          <template #default="{ row }">{{ $money(row.%s) }}</template>\n'
                    '        </el-table-column>' % (m.group(1), prop))
        s = pat.sub(repl, s)
    if n:
        io.open(p, 'w', encoding='utf-8', newline='').write(s)
        print(fn, '转换', n, '列')
