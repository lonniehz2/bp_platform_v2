# -*- coding: utf-8 -*-
"""菜单/页面改名：授权与对账 → 通行授权；来访登记 → 入户走访。

同步位置：路由标题、组内分区名、菜单说明、帮助文案、页面标题与提示。
"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FE = os.path.join(ROOT, 'frontend', 'src')

# ---------- 1) 路由标题 ----------
P = os.path.join(FE, 'router', 'index.js')
s = io.open(P, encoding='utf-8').read()
n = 0
for a, b in [("title: '授权与对账'", "title: '通行授权'"),
             ("title: '来访登记'", "title: '入户走访'")]:
    if a in s:
        s = s.replace(a, b)
        n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('路由标题替换:', n)

# ---------- 2) 菜单配置：分区名 + 说明 ----------
P = os.path.join(FE, 'layout', 'menuConfig.js')
s = io.open(P, encoding='utf-8').read()
n = 0
PAIRS = [
    ("{ title: '门禁通行', paths: ['/access', '/keyring', '/grants'] }",
     "{ title: '通行与授权', paths: ['/access', '/keyring', '/grants'] }"),
    ("'/grants': '发卡授权任务与下发对账',",
     "'/grants': '通行权限的新建、撤销与对账审计',"),
    ("'/visits': '来访登记与出入记录',",
     "'/visits': '入户核查房屋使用情况（转租/空置/违规）',"),
]
for a, b in PAIRS:
    if a in s:
        s = s.replace(a, b)
        n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('菜单配置替换:', n)

# ---------- 3) 访问页面：标题与提示 ----------
P = os.path.join(FE, 'views', 'Visits.vue')
s = io.open(P, encoding='utf-8').read()
n = 0
for a, b in [
    ('<h3 style="margin:0">来访登记</h3>', '<h3 style="margin:0">入户走访</h3>'),
    (":title=\"'来访登记用于园区/小区出入管理，可关联被访人'\"",
     ':title="\'用于定期入户核查房屋使用情况：是否居住、实际人数、是否转租/空置/违规使用\'"'),
    ('登记来访', '走访登记'),
]:
    if a in s:
        s = s.replace(a, b)
        n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('入户走访页改写:', n)

# ---------- 4) 帮助文案 ----------
P = os.path.join(FE, 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()
n = 0
for a, b in [
    ('来访登记', '入户走访'),
    ('授权与对账', '通行授权'),
]:
    if a in s:
        s = s.replace(a, b)
        n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助文案替换:', n)
