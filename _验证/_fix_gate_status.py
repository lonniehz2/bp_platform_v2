# -*- coding: utf-8 -*-
"""修正测试状态为 REVIEWING（isInReview 允许 ACCEPTED/REVIEWING/SUPPLEMENT）"""
import io

p = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'
     r'\ApplicationQualifyGateTest.java')
s = io.open(p, encoding='utf-8').read()

old = 'e.setApplicationStatus("DEPT_REVIEW");'
new = '// isInReview() 允许 ACCEPTED / REVIEWING / SUPPLEMENT\n        e.setApplicationStatus("REVIEWING");'
assert old in s, '锚点缺失：未找到 DEPT_REVIEW'
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print('已改为 REVIEWING')
