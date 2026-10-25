# -*- coding: utf-8 -*-
"""补齐审计日志枚举（按行替换，避免转义问题）。"""
import io
import os

E = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 'frontend', 'src', 'constants', 'enums.js')
lines = io.open(E, encoding='utf-8').read().split('\n')

target_idx = None
for i, ln in enumerate(lines):
    if ln.strip().startswith('auditLevel:'):
        target_idx = i
        break

if target_idx is None:
    print('未找到 auditLevel 行')
    raise SystemExit(1)

NEW = [
    "  auditType: {",
    "    DATA: '数据变更',",
    "    SECURITY: '安全事件',",
    "    CONFIG: '配置变更',",
    "    LOGIN: '登录行为',",
    "    FINANCE: '财务操作',",
    "    SYSTEM: '系统操作'",
    "  },",
    "  auditLevel: {",
    "    INFO: '提示',",
    "    WARNING: '警告',",
    "    IMPORTANT: '重要',",
    "    CRITICAL: '严重'",
    "  },"
]

lines[target_idx:target_idx + 1] = NEW
io.open(E, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
print('已在第 %d 行插入 auditType 与 auditLevel.IMPORTANT' % (target_idx + 1))
