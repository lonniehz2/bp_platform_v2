# -*- coding: utf-8 -*-
"""修正验证脚本：时间格式 + 数字按字符串比较（Long 序列化为 String）"""
import io

p = r'D:\Work\业务平台开发\_验证\_verify_dev.py'
s = io.open(p, encoding='utf-8').read()

# 1) 时间格式改为 yyyy-MM-dd HH:mm:ss
s = s.replace("+ 'T09:00:00'", "+ ' 09:00:00'")
s = s.replace("+ 'T18:30:00'", "+ ' 18:30:00'")
s = s.replace("+ 'T23:50:00'", "+ ' 23:50:00'")
s = s.replace("+ 'T12:00:00'", "+ ' 12:00:00'")
s = s.replace("+ 'T08:00:00'", "+ ' 08:00:00'")
s = s.replace(".find('T08:00')", ".find('08:00')")

# 2) 数字统一转 int（本项目 Long 序列化为字符串）
s = s.replace("chk('⭐⭐ 不可信占比统计', ur.get('total', 0) >= 5, ur.get('total'))",
              "chk('⭐⭐ 不可信占比统计', int(ur.get('total') or 0) >= 5, ur.get('total'))")
s = s.replace("chk('不可信计数正确（临时密码1条）', ur.get('untrusted') == 1, ur.get('untrusted'))",
              "chk('不可信计数正确（临时密码1条）', "
              "int(ur.get('untrusted') or 0) == 1, ur.get('untrusted'))")
s = s.replace("chk('⭐ 轨迹统计异常次数', tr.get('abnormalRecords') == 1, tr.get('abnormalRecords'))",
              "chk('⭐ 轨迹统计异常次数', "
              "int(tr.get('abnormalRecords') or 0) == 1, tr.get('abnormalRecords'))")
s = s.replace("chk('⭐ 批量上报', r.get('data') == 2, r.get('data'))",
              "chk('⭐ 批量上报', int(r.get('data') or 0) == 2, r.get('data'))")

io.open(p, 'w', encoding='utf-8').write(s)
print('测试已修正（时间格式 + 数字类型）')
