# -*- coding: utf-8 -*-
"""文档一致性检查：手册提到的页面/接口必须存在；页面必须被手册覆盖。

匹配方式：
  · 页面按「路由路径」或「菜单标题（meta.title）」任一共现即算覆盖
  · 手册中反引号包裹的路径 /api/v1/... 必须是真实接口
输出不一致清单；一致时退出码 0。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
FRONT = os.path.join(ROOT, 'frontend', 'src')
JAVA = os.path.join(ROOT, 'backend', 'src', 'main', 'java', 'com', 'yundao', 'bp')
DOCS = ['10_业务操作流程与验收手册.md', '11_一期交付清单.md']

router = io.open(os.path.join(FRONT, 'router', 'index.js'), encoding='utf-8').read()
# 解析 { path, meta.title } 组合
pages = []
for m in re.finditer(r"path:\s*'([^']+)'[\s\S]{0,300}?title:\s*'([^']+)'", router):
    path, title = m.group(1), m.group(2)
    if path.startswith('/') and path not in ('/', '/login'):
        pages.append((path.split('/:')[0], title))

api_paths = set()
for dirpath, _, files in os.walk(JAVA):
    for fn in files:
        if not fn.endswith('Controller.java'):
            continue
        s = io.open(os.path.join(dirpath, fn), encoding='utf-8').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)\s*public class', s)
        base = m.group(1) if m else ''
        for mm in re.finditer(r'@(Get|Post|Put|Delete)Mapping(?:\("([^"]*)"\))?', s):
            sub = mm.group(2) or ''
            api_paths.add((base.rstrip('/') + '/' + sub.lstrip('/')).rstrip('/'))

doc_text = ''
for d in DOCS:
    p = os.path.join(ROOT, d)
    if os.path.exists(p):
        doc_text += io.open(p, encoding='utf-8').read()

issues = []
print('=' * 60)
print(' 文档一致性检查')
print('=' * 60)
print('页面 %d 个，后端接口 %d 个' % (len(pages), len(api_paths)))

# 1) 未被手册覆盖的页面（路径与标题都要出现才算覆盖）
undoc = []
for path, title in pages:
    if path in doc_text or title in doc_text:
        continue
    # 手册可能只写标题的一部分（如「账单与缴费」写作「账单」）
    if any(part in doc_text for part in title.replace('/', '').split() if len(part) >= 2):
        continue
    undoc.append('%s(%s)' % (title, path))
if undoc:
    issues.append('未被手册覆盖的页面 %d 个：%s' % (len(undoc), '、'.join(undoc[:12])))

# 2) 手册提到但不存在的页面路径
doc_paths = {r.rstrip('/') for r in re.findall(r'`(/[a-z][a-z0-9\-/]*)`', doc_text)
             if not r.startswith('/api')}
known_first = {x[0].split('/')[1] for x in pages if x[0].count('/') >= 1}
ghost = sorted(p for p in doc_paths
               if p not in {x[0] for x in pages}
               and p.split('/')[1:2] and p.split('/')[1] in known_first)
if ghost:
    issues.append('手册提到但不存在：%s' % '、'.join(ghost[:10]))

# 3) 手册提到的接口必须存在
doc_apis = {a for a in re.findall(r'`(/api/v1[a-z0-9\-/{}\.]*)`', doc_text)}
bad_api = []
for a in doc_apis:
    norm = re.sub(r'\{[^}]+\}', '{id}', a.rstrip('/'))
    if not any(re.sub(r'\{[^}]+\}', '{id}', real) == norm
               or re.sub(r'\{[^}]+\}', '{id}', real).startswith(norm + '/')
               for real in api_paths):
        bad_api.append(a)
if bad_api:
    issues.append('手册提到的接口不存在：%s' % '、'.join(sorted(bad_api)[:10]))

print()
if issues:
    for i in issues:
        print('  ✘ ' + i)
    print('\n结论：%d 类不一致' % len(issues))
    sys.exit(1)
print('  ✔ 手册与实现一致')
sys.exit(0)
