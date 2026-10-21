# -*- coding: utf-8 -*-
"""修正页面检查：动态拼接路径不算失效；补 MENU_RANK"""
import io
import re

# ---------- 1) 检查脚本：动态路径单独归类 ----------
P = r'D:\Work\业务平台开发\_验证\_check_pages.py'
s = io.open(P, encoding='utf-8').read()

s = s.replace('''bad_calls = {}
for r in matrix:
    if not r['file']:
        continue
    s = io.open(r['file'], encoding='utf-8').read()
    for m in re.finditer(r"req\\.(get|post|put|delete)\\(\\s*[`'\\"]([^`'\\"]*)", s):
        path = m.group(2)
        if not path.startswith('/api/'):
            path = '/api/v1' + path
        if (norm(path), m.group(1).upper()) not in backend:
            bad_calls.setdefault(r['title'], set()).add(
                '%s %s' % (m.group(1).upper(), path))''',
              '''bad_calls = {}
dynamic_calls = set()
for r in matrix:
    if not r['file']:
        continue
    s = io.open(r['file'], encoding='utf-8').read()
    for m in re.finditer(r"req\\.(get|post|put|delete)\\(\\s*[`'\\"]([^`'\\"]*)", s):
        path = m.group(2)
        # 模板拼接 / 变量路径无法静态判定，单独统计（需人工核对）
        if '${' in path or 'pathTpl' in path:
            dynamic_calls.add('%s %s' % (m.group(1).upper(), path[:60]))
            continue
        if not path.startswith('/api/'):
            path = '/api/v1' + path
        if (norm(path), m.group(1).upper()) not in backend:
            bad_calls.setdefault(r['title'], set()).add(
                '%s %s' % (m.group(1).upper(), path))''')

s = s.replace('''else:
    print('   ✔ 无失效路径（后端 %d 个接口）' % len(backend))''',
              '''else:
    print('   ✔ 无失效路径（后端 %d 个接口）' % len(backend))
if dynamic_calls:
    print('   ○ 动态拼接路径 %d 处（静态不可判定，需人工核对）：%s'
          % (len(dynamic_calls), '; '.join(sorted(dynamic_calls)[:3])))''')

io.open(P, 'w', encoding='utf-8').write(s)
print('  ✓ 检查脚本：动态路径与失效路径分开统计')

# ---------- 2) Layout：补 MENU_RANK ----------
L = r'D:\Work\业务平台开发\frontend\src\layout\Layout.vue'
t = io.open(L, encoding='utf-8').read()
if "'/ops-extras'" not in t:
    t = t.replace("  '/open': 74, '/gov': 75",
                  "  '/open': 74, '/gov': 75, '/ops-extras': 76")
    io.open(L, 'w', encoding='utf-8').write(t)
    print('  ✓ MENU_RANK 补 /ops-extras')
else:
    print('  - MENU_RANK 已含 /ops-extras')
