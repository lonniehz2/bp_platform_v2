# -*- coding: utf-8 -*-
"""修正审核阶段为 FINAL（真实枚举 ACCEPT/FORM/JOINT/FINAL）"""
import io

p = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'
     r'\ApplicationQualifyGateTest.java')
s = io.open(p, encoding='utf-8').read()

n = s.count('"DEPT"')
s = s.replace('new ReviewCmd("DEPT",', 'new ReviewCmd("FINAL",')
io.open(p, 'w', encoding='utf-8').write(s)
print('替换 "DEPT" → "FINAL"：%d 处' % n)
