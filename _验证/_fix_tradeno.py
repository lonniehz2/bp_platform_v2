# -*- coding: utf-8 -*-
"""修正 pid 为字符串导致的格式化错误"""
import io

P = r'D:\Work\业务平台开发\_验证\_seed_testdata7.py'
s = io.open(P, encoding='utf-8').read()
old = "'tradeNo': 'TN%d' % (pid % 1000000),"
new = "'tradeNo': 'TN%d' % (int(pid) % 1000000),"
if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已修正：int(pid)')
else:
    print('未找到目标行，当前内容：')
    for ln in s.split('\n'):
        if 'tradeNo' in ln:
            print('  ' + ln.strip())
