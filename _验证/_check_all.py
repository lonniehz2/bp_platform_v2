# -*- coding: utf-8 -*-
"""一键验收：路径核对 + 显示层一致性 + 冒烟

用法：
  python _check_all.py            # 常规验收
  python _check_all.py --strict   # 任一项失败即非 0（CI 用）
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
STRICT = ['--strict'] if '--strict' in sys.argv else []

STEPS = [
    ('前端构建与静态校验', '_check_build.py', STRICT),
    ('ID 字段精度（禁止 Number 转 ID）', '_check_id_number.py', []),
    ('接口路径核对（前后端一致性）', '_check_api_paths.py', STRICT),
    ('查询参数接线（前端传的键后端必须认）', '_audit_params.py', ['--strict']),
    ('显示层一致性（字段/枚举/ID/树）', '_check_display.py', STRICT),
    ('数据范围扫描（列表接口必须限权）', '_check_datascope.py', STRICT),
    ('全功能页面对照（46 项）', '_verify_all_pages.py', []),
]

results = []
print('=' * 78)
print(' 平台验收检查')
print('=' * 78)

for name, script, extra in STEPS:
    path = os.path.join(HERE, script)
    print('\n▶ %s  (%s)' % (name, script))
    if not os.path.exists(path):
        print('  ✗ 脚本不存在')
        results.append((name, 2))
        continue
    p = subprocess.run([PY, path] + extra, cwd=HERE)
    results.append((name, p.returncode))

print('\n' + '=' * 78)
print(' 汇总')
print('=' * 78)
for name, code in results:
    mark = '✔' if code == 0 else ('⚠' if code == 2 else '✗')
    print('  %s %-34s 退出码 %d' % (mark, name, code))

failed = [n for n, c in results if c != 0]
if failed:
    print('\n 未通过：%s' % ', '.join(failed))
    sys.exit(1)
print('\n ✔ 全部通过')
sys.exit(0)
