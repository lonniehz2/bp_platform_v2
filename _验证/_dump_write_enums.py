# -*- coding: utf-8 -*-
"""查真实枚举值 + 年审复核异常日志"""
import io
import os
import re
import subprocess
import sys

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

TARGETS = {
    'ComplaintCreateCmd': ['complaintType', 'source'],
    'AlertCreateCmd': ['alertLevel', 'alertCategory', 'alertType'],
    'VisitCreateCmd': ['visitType'],
    'CreditCreateCmd': ['bizType', 'sanctionType', 'violationType'],
}

for cls, fields in TARGETS.items():
    for root, _, fs in os.walk(J):
        if cls + '.java' not in fs:
            continue
        s = io.open(os.path.join(root, cls + '.java'), encoding='utf-8').read()
        print('\n■ %s' % cls)
        for fld in fields:
            # 找该字段上方的 @Pattern
            m = re.search(r'@Pattern\(regexp\s*=\s*"([^"]+)"[^)]*\)\s*(?:@\w+[^\n]*\s*)*'
                          r'[\w<>]+\s+' + fld + r'\b', s)
            if m:
                vals = m.group(1).replace('^$|', '')
                print('   %-18s %s' % (fld, vals))
            else:
                # 宽松：找字段行前 200 字符内的 Pattern
                i = s.find(' ' + fld + ',')
                if i < 0:
                    i = s.find(' ' + fld + ')')
                seg = s[max(0, i - 260):i] if i > 0 else ''
                pm = re.findall(r'regexp\s*=\s*"([^"]+)"', seg)
                print('   %-18s %s' % (fld, pm[-1].replace('^$|', '') if pm else '（无约束）'))
        # 必填字段
        req = re.findall(r'@NotBlank\([^)]*\)\s*[\w<>]+\s+(\w+)', s)
        print('   必填：%s' % (', '.join(req) or '无'))
        break

print('\n' + '=' * 70)
print(' 年审复核异常日志')
p = subprocess.run(
    [sys.executable, 'vm.py',
     "grep -A6 'annual-reviews' /var/log/bp-platform/app.log | "
     "grep -iE 'Caused by|Exception|Error' | tail -5"],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd=r'D:\Work\业务平台开发\_验证')
print((p.stdout or p.stderr or '')[-1200:])
