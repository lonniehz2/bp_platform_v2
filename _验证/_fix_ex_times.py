# -*- coding: utf-8 -*-
"""修正 ExchangeServiceImpl 残留的 MAX_EXCHANGE_TIMES 引用"""
import io

p = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\biz\service\impl\ExchangeServiceImpl.java')
s = io.open(p, encoding='utf-8').read()
old = 'Math.max(0, MAX_EXCHANGE_TIMES - done - 1));'
new = 'Math.max(0, maxTimes - done - 1));'
assert old in s, '锚点缺失'
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('已修正：MAX_EXCHANGE_TIMES → maxTimes')
