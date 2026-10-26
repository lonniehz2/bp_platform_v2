# -*- coding: utf-8 -*-
"""适配新菜单架构的两个静态检查修正。

1) _check_build.py：v-for 支持无括号别名（v-for="sec in activeSections"）
2) _check_menu.py：菜单已改为「路由 meta 驱动」，不再维护路径白名单，
   判定改为「useMenu 是否按 meta.group 分组」。
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- 1) _check_build.py ----------
P = os.path.join(HERE, '_check_build.py')
s = io.open(P, encoding='utf-8').read()
if 'v-for 的局部变量' in s and 'sec in' not in s:
    OLD = """    for m in re.finditer(r'v-for\\s*=\\s*"[^"]*?\\bin\\b', tpl):
        seg = m.group(0)
        names = re.findall(r'\\(([^)]*)\\)', seg)
        if names:
            for part in names[0].split(','):
                n = part.strip()
                if re.fullmatch(r'[A-Za-z_$][\\w$]*', n or ''):
                    defined.add(n)"""
    NEW = """    for m in re.finditer(r'v-for\\s*=\\s*"([^"]*?)"', tpl):
        expr = m.group(1)
        head = expr.split(' in ')[0].strip()
        # 形式一：(item, i) in list ；形式二：item in list
        if head.startswith('(') and head.endswith(')'):
            head = head[1:-1]
        for part in head.split(','):
            n = part.strip()
            if re.fullmatch(r'[A-Za-z_$][\\w$]*', n or ''):
                defined.add(n)"""
    if OLD in s:
        s = s.replace(OLD, NEW, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('_check_build：v-for 两种写法都支持')
    else:
        print('_check_build：锚点不匹配')

# ---------- 2) _check_menu.py ----------
P = os.path.join(HERE, '_check_menu.py')
s = io.open(P, encoding='utf-8').read()
if 'meta 驱动' not in s:
    OLD = """    # 兜底逻辑存在时，meta.group 也会进菜单
    if 'GROUP_ALIAS[m.meta?.group]' in menu:
        continue"""
    NEW = """    # 新架构：菜单由路由 meta.group 驱动（无路径白名单），
    # 只要 useMenu 按 groupNameOf(meta) 分组，所有带 meta.group 的路由都会出现
    if 'groupNameOf(' in menu and 'm.meta' in menu:
        continue"""
    if OLD in s:
        s = s.replace(OLD, NEW, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('_check_menu：改为 meta 驱动判定')
    else:
        print('_check_menu：锚点不匹配')
