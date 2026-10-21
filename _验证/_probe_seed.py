# -*- coding: utf-8 -*-
"""探测 DB 可达性 + 提取 open/gov 权限码"""
import os
import re
import socket

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

print('=== DB 可达性 ===')
for host, port in (('192.168.31.153', 33306), ('192.168.31.153', 3306)):
    try:
        s = socket.create_connection((host, port), timeout=4)
        s.close()
        print('  %s:%s  OK' % (host, port))
    except Exception as e:
        print('  %s:%s  FAIL %s' % (host, port, type(e).__name__))

print()
print('=== open/gov 控制器引用的权限码 ===')
codes = set()
for pkg in ('open', 'gov'):
    d = os.path.join(BASE, pkg, 'controller')
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        if not f.endswith('.java'):
            continue
        s = open(os.path.join(d, f), encoding='utf-8').read()
        for m in re.finditer(r'@RequirePerm\("([^"]+)"\)', s):
            codes.add(m.group(1))
            print('  %-24s %s' % (m.group(1), f))
print()
print('共 %d 个权限码：%s' % (len(codes), ', '.join(sorted(codes))))
