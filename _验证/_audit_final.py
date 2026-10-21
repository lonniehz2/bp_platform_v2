# -*- coding: utf-8 -*-
"""最终审计：菜单分组完整性 + 页面可达性汇总"""
import io
import os
import re
from collections import OrderedDict

FE = r'D:\Work\业务平台开发\frontend\src'
R = os.path.join(FE, 'router', 'index.js')
s = io.open(R, encoding='utf-8').read()

items = []
for m in re.finditer(r"path:\s*'/([a-z\-]+)',([\s\S]{0,420}?)meta:\s*\{([^}]*)\}", s):
    path, meta = m.group(1), m.group(3)
    t = re.search(r"title:\s*'([^']+)'", meta)
    g = re.search(r"group:\s*'([^']+)'", meta)
    p = re.search(r"perm:\s*'([^']+)'", meta)
    if not t:
        continue
    items.append({'path': path, 'title': t.group(1),
                  'group': g.group(1) if g else '未分组',
                  'perm': p.group(1) if p else None})

ORDER = ['运营监控', '申请与配租', '合同与财务', '资产与设备', '人员与服务', '系统与集成']
g = OrderedDict((k, []) for k in ORDER)
for x in items:
    g.setdefault(x['group'], []).append(x)

print('=' * 66)
print(' SPA 菜单结构（共 %d 项）' % len(items))
print('=' * 66)
for name, arr in g.items():
    if not arr:
        continue
    print('\n【%s】%d 项' % (name, len(arr)))
    for x in arr:
        print('   /%-18s %-12s %s'
              % (x['path'], x['title'], ('🔒 ' + x['perm']) if x['perm'] else ''))

views = [f[:-4] for f in os.listdir(os.path.join(FE, 'views')) if f.endswith('.vue')]
comp = set(re.findall(r"import\('@/views/(\w+)\.vue'\)", s))
print('\n' + '=' * 66)
print(' 视图 %d ｜ 被路由引用 %d ｜ 未被引用 %s'
      % (len(views), len(comp & set(views)),
         [v for v in views if v not in comp] or '无（Login 为登录页，单独定义）'))
print(' 受权限控制的菜单：%d 项（admin 全可见，viewer 会隐藏部分）'
      % len([x for x in items if x['perm']]))
