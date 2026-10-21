# -*- coding: utf-8 -*-
"""带行号运行种子脚本，定位失败语句"""
import subprocess
import sys

p = subprocess.run(
    [sys.executable, '_seed_open_gov.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace',
    cwd=r'D:\Work\业务平台开发\_验证')

lines = (p.stderr or '').split('\n')
for i, ln in enumerate(lines):
    if '_seed_open_gov.py", line' in ln:
        print('→ ' + ln.strip())
        # 打印其后 4 行（源码行）
        for j in range(i + 1, min(i + 5, len(lines))):
            if lines[j].strip():
                print('   ' + lines[j].rstrip())
        break
else:
    print('未定位到行号，尾部输出：')
    print('\n'.join(lines[-6:]))
