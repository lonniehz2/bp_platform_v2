# -*- coding: utf-8 -*-
"""修正 GovReportTask：不存在 setFinish，实际用 reportTime"""
import io

p = (r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
     r'\gov\service\impl\GovReportServiceImpl.java')
s = io.open(p, encoding='utf-8').read()

before = s.count('setFinish(')
s = s.replace('t.setFinish(now);', 't.setReportTime(now);')
s = s.replace('t.setFinish(LocalDateTime.now());', 't.setReportTime(LocalDateTime.now());')
# 第 339 行的残留（若上面未覆盖）
s = s.replace('.setFinish(', '.setReportTime(')
after = s.count('setFinish(')

io.open(p, 'w', encoding='utf-8').write(s)
print('setFinish 出现次数：%d → %d（已改为 setReportTime）' % (before, after))

# 同时检查 reportTime 是否有重复赋值（同一事务内两次赋值无意义）
n = s.count('setReportTime(')
print('setReportTime 调用次数：%d' % n)
