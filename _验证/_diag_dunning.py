# -*- coding: utf-8 -*-
"""排查催缴 scan 异常 + 导出补贴标准/催缴 DTO 字段"""
import io
import os
import re
import subprocess
import sys

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

print('=== 催缴 scan 相关 DTO ===')
for rel in ('fin/dto/DunningCreateCmd.java', 'fin/dto/SubsidyStandardCreateCmd.java'):
    p = os.path.join(JAVA, rel.replace('/', os.sep))
    if not os.path.exists(p):
        print('  □ %s 不存在' % rel)
        continue
    s = io.open(p, encoding='utf-8').read()
    m = re.search(r'record\s+(\w+)\s*\((.*?)\)\s*\{', s, re.S)
    print('  ■ %s' % rel)
    if m:
        for ln in re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S).split('\n'):
            t = ln.strip().rstrip(',')
            if t:
                print('     ' + t[:110])

print('\n=== 最近异常（催缴 scan）===')
p = subprocess.run(
    [sys.executable, 'vm.py',
     "grep -A6 'BP99999\\|scan' /var/log/bp-platform/app.log | "
     "grep -iE 'Caused by|Exception|Error|dunning|dunnings' | tail -6"],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd=r'D:\Work\业务平台开发\_验证')
print((p.stdout or p.stderr or '')[-1500:])
