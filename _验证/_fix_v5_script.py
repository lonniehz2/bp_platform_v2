# -*- coding: utf-8 -*-
"""修正 v5 脚本中的跨行字符串"""
import io

P = r'D:\Work\业务平台开发\_验证\_upd_report_v5.py'
s = io.open(P, encoding='utf-8').read()

old = """        "w('> 距可交付仅剩：**微信小程序**（H5 已覆盖主要租客场景，可作为过渡）'
        '与**真机联调**。')", 1)"""

new = """        "w('> 距可交付仅剩：**微信小程序**（H5 已覆盖主要租客场景，可作为过渡）"
        "与**真机联调**。')", 1)"""

if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已修正跨行字符串')
else:
    # 兜底：按行定位
    lines = s.split('\n')
    for i, ln in enumerate(lines):
        if '距可交付仅剩：**微信小程序**' in ln:
            lines[i] = ('        "w(\'> 距可交付仅剩：**微信小程序**（H5 已覆盖主要租客场景，'
                        '可作为过渡）"')
            if i + 1 < len(lines) and '与**真机联调**' in lines[i + 1]:
                lines[i + 1] = '        "与**真机联调**。\')", 1)'
            break
    io.open(P, 'w', encoding='utf-8').write('\n'.join(lines))
    print('已按行修正')
