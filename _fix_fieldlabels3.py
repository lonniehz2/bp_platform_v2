# -*- coding: utf-8 -*-
"""补齐最后 6 个计算字段中文名"""
import io
import re

P = r'D:\Work\业务平台开发\frontend\src\constants\fieldLabels.js'
s = io.open(P, encoding='utf-8').read()

NEW = {
    'unpaidAmount': '未缴金额',
    'readyToComplete': '可办理完成',
    'real': '是否真实',
    'responseOverdue': '响应超时',
    'underBan': '处于失信禁申期',
    'matched': '已匹配',
}

added = []
for k, v in NEW.items():
    if re.search(r"^\s{2}%s:\s*'" % k, s, re.M):
        continue
    added.append((k, v))

if added:
    block = '\n'.join("  %s: '%s'," % (k, v) for k, v in added)
    # 插到 FIELD_LABEL 开头（计算字段区块之后）
    anchor = "export const FIELD_LABEL = {\n"
    s = s.replace(anchor, anchor + block + '\n', 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ 补 %d 个：%s' % (len(added), ', '.join(k for k, _ in added)))
else:
    print('  - 均已存在')

# 语法自检：确认每行都有逗号
bad = []
for i, ln in enumerate(s.split('\n'), 1):
    if re.fullmatch(r"\s{2}\w+:\s*'[^']*'", ln.rstrip()):
        bad.append(i)
print('  缺逗号行：%s' % (bad or '无'))
