# -*- coding: utf-8 -*-
"""修正断言：终审通过后状态是 APPROVED（不是 QUALIFIED）"""
import io

p = (r'D:\Work\业务平台开发\backend\src\test\java\com\yundao\bp\biz'
     r'\ApplicationQualifyGateTest.java')
s = io.open(p, encoding='utf-8').read()

n = s.count('"QUALIFIED"')
s = s.replace('assertEquals("QUALIFIED", vo.applicationStatus(), level + " 应通过");',
              'assertEquals("APPROVED", vo.applicationStatus(), level + " 应通过");')
s = s.replace('''        assertEquals("QUALIFIED",
                service.review(100L, pass(), 1001L, "审核员").applicationStatus());''',
              '''        assertEquals("APPROVED",
                service.review(100L, pass(), 1001L, "审核员").applicationStatus());''')
io.open(p, 'w', encoding='utf-8').write(s)
print('原 "QUALIFIED" 出现 %d 处，已改为 APPROVED' % n)
