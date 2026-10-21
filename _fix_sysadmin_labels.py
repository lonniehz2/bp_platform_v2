# -*- coding: utf-8 -*-
"""修复 SysAdmin 硬编码英文级别选项"""
import io
import re

P = r'D:\Work\业务平台开发\frontend\src\views\SysAdmin.vue'
s = io.open(P, encoding='utf-8').read()

FIX = {
    'CRITICAL': '严重',
    'IMPORTANT': '重要',
    'NORMAL': '普通',
}
n = 0
for code, cn in FIX.items():
    old = '<el-option label="%s" value="%s"' % (code, code)
    new = '<el-option label="%s" value="%s"' % (cn, code)
    if old in s:
        s = s.replace(old, new)
        n += 1
        print('  ✓ %s → %s' % (code, cn))
    else:
        # 也处理 label/value 顺序颠倒或含空格
        m = re.search(r'<el-option[^>]*value="%s"[^>]*>' % code, s)
        if m and 'label="%s"' % code in m.group(0):
            s = s.replace(m.group(0), m.group(0).replace('label="%s"' % code,
                                                         'label="%s"' % cn))
            n += 1
            print('  ✓ %s → %s（变体）' % (code, cn))

io.open(P, 'w', encoding='utf-8').write(s)
print('\n  共修 %d 处' % n)

for ln in s.split('\n'):
    if 'el-option' in ln and ('CRITICAL' in ln or 'IMPORTANT' in ln or 'NORMAL' in ln):
        print('  ' + ln.strip()[:110])
