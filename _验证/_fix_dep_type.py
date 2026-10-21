# -*- coding: utf-8 -*-
"""给 refund() 辅助方法补 refundType=DEPOSIT"""
import io

p = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\fin'
     r'\DepositRefundTest.java')
s = io.open(p, encoding='utf-8').read()

if 'setRefundType("DEPOSIT")' in s:
    print('已存在，跳过')
else:
    old = ('        r.setRefundAmount(new BigDecimal(amount));\n'
           '        r.setRefundStatus(status);')
    new = ('        r.setRefundAmount(new BigDecimal(amount));\n'
           '        // 必须标记为押金退还，否则 completeRefund 不会回写押金台账\n'
           '        r.setRefundType("DEPOSIT");\n'
           '        r.setRefundStatus(status);')
    assert old in s, '锚点缺失'
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8').write(s)
    print('已补 refundType=DEPOSIT')
