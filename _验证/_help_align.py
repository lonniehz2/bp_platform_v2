# -*- coding: utf-8 -*-
"""帮助章节标题与新旧菜单名对齐。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()

PAIRS = [
    # 章节标题
    ("title: '二、运营总览'", "title: '二、工作台'"),
    ("title: '三、保障对象'", "title: '三、保障与资格'"),
    ("title: '四、资格准入'", "title: '四、申请与配租'"),
    ("title: '五、合同管理'", "title: '五、合同与租赁'"),
    ("title: '六、账务收费'", "title: '六、收费与账务'"),
    ("title: '七、资产与设备'", "title: '七、房源与设备'"),
    ("title: '九、系统与集成'", "title: '九、系统与数据'"),
    # 正文中的菜单路径
    ("系统与集成 → 用户与权限", "系统与数据 → 用户与权限"),
    ("系统与集成 → 使用帮助", "系统与数据 → 使用帮助"),
    ("「系统与集成 → 用户与权限」", "「系统与数据 → 用户与权限」"),
    ("「保障对象 → 人员档案」", "「保障与资格 → 人员档案」"),
    ("「系统与集成 → 用户与权限」中", "「系统与数据 → 用户与权限」中"),
    ("进入「系统与集成」", "进入「系统与数据」"),
    ("进入「账务收费」", "进入「收费与账务」"),
    ("进入「资产与设备」", "进入「房源与设备」"),
]

n = 0
for a, b in PAIRS:
    if a in s and a != b:
        s = s.replace(a, b)
        n += 1

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助文本已对齐，替换组数:', n)
