# -*- coding: utf-8 -*-
"""审计 SPA 完整性：路由 / 视图文件 / 菜单渲染 三者比对"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'
ROUTER = os.path.join(FE, 'router', 'index.js')
VIEWS = os.path.join(FE, 'views')
LAYOUT = os.path.join(FE, 'layout', 'Layout.vue')

r = io.open(ROUTER, encoding='utf-8').read()

# 1) 路由条目
routes = []
for m in re.finditer(r"path:\s*'([^']+)',\s*\n\s*name:\s*'([^']+)',\s*\n\s*"
                     r"component:\s*\(\)\s*=>\s*import\('@/views/(\w+)\.vue'\),\s*\n\s*"
                     r"meta:\s*\{\s*title:\s*'([^']+)'", r):
    routes.append({'path': m.group(1), 'name': m.group(2),
                   'comp': m.group(3), 'title': m.group(4)})
print('路由条目：%d' % len(routes))

# 2) 视图文件
files = sorted(f[:-4] for f in os.listdir(VIEWS) if f.endswith('.vue'))
print('视图文件：%d' % len(files))

# 3) 菜单：Layout.vue 如何渲染
lay = io.open(LAYOUT, encoding='utf-8').read()
print('\n=== Layout.vue 菜单渲染方式 ===')
if 'v-for' in lay and ('routes' in lay or '$router' in lay or 'menuList' in lay):
    for m in re.finditer(r'(menuList|routes|allRoutes)[^=\n]*=\s*([^\n]{0,120})', lay):
        print('  %s' % m.group(0)[:130])
    print('  → 若为动态生成，菜单自动覆盖路由')
else:
    print('  → 未发现动态渲染，可能是硬编码')

# 4) 菜单里硬编码的项（找 el-menu-item / el-sub-menu）
menu_titles = re.findall(r'<(?:el-menu-item|el-sub-menu)[^>]*>\s*([^<>{]{1,20})\s*<', lay)
menu_titles = [x.strip() for x in menu_titles if x.strip()]
print('\n菜单硬编码文本 %d 项：%s' % (len(menu_titles), menu_titles[:20]))

print('\n' + '=' * 70)
print(' 比对结果')
print('=' * 70)

comp_set = {x['comp'] for x in routes}
orphan = [f for f in files if f not in comp_set]
missing_file = [x['comp'] for x in routes if x['comp'] not in files]

print('\n① 有视图但无路由（页面做出来但访问不到）：%d' % len(orphan))
for f in orphan:
    print('    %s.vue' % f)

print('\n② 有路由但缺视图文件：%d' % len(missing_file))
for f in missing_file:
    print('    %s.vue' % f)

# 5) 菜单是否覆盖全部路由
print('\n③ 路由列表（%d 条）' % len(routes))
for x in routes:
    print('    %-18s %-20s %s' % (x['path'], x['comp'], x['title']))
