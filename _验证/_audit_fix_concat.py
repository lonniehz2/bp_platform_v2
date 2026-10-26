# -*- coding: utf-8 -*-
"""改进前端路径抽取：支持字符串拼接写法（'/x/' + id + '/submit'）。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_audit_api_ui.py')
s = io.open(P, encoding='utf-8').read()

OLD = """CALL_RE = re.compile(r"\\breq\\.(get|post|put|delete)\\s*\\(\\s*[`'\\"]([^`'\\"]+)[`'\\"]")"""
NEW = """CALL_RE = re.compile(r"\\breq\\.(get|post|put|delete)\\s*\\(([^\\n]{0,200})")"""

if OLD in s:
    s = s.replace(OLD, NEW, 1)

    OLD_BLOCK = """        for mm in CALL_RE.finditer(src):
            method = mm.group(1).upper()
            raw = mm.group(2)
            p = re.sub(r'\\$\\{[^}]*\\}', '{x}', raw)
            p = re.sub(r'\\{[^}]*\\}', '{x}', p)
            p = p.split('?')[0]   # 去掉查询串，只比路径
            if not p.startswith('/'):
                p = '/' + p
            p = re.sub(r'/+', '/', p)
            if len(p) > 1 and p.endswith('/'):
                p = p[:-1]
            front.append((method, p, rel))"""

    NEW_BLOCK = """        for mm in CALL_RE.finditer(src):
            method = mm.group(1).upper()
            expr = mm.group(2)
            # 截到第一个顶层逗号/右括号，避免把 body 参数一起吃进来
            depth, cut = 0, len(expr)
            for i, ch in enumerate(expr):
                if ch in '([{':
                    depth += 1
                elif ch in ')]}':
                    if depth == 0:
                        cut = i
                        break
                    depth -= 1
                elif ch == ',' and depth == 0:
                    cut = i
                    break
            expr = expr[:cut]
            e2 = re.sub(r'\\$\\{[^}]*\\}', '{x}', expr)
            segs = re.findall(r"[`'\\"]([^`'\\"]*)[`'\\"]", e2)
            if not segs:
                continue
            if '+' in e2 and len(segs) > 1:
                # '/a/' + id + '/b' → /a/{x}/b
                p = '{x}'.join(segs)
            else:
                p = ''.join(segs)
            p = re.sub(r'\\{[^}]*\\}', '{x}', p)
            p = p.split('?')[0]
            if not p.startswith('/'):
                p = '/' + p
            p = re.sub(r'/+', '/', p)
            if len(p) > 1 and p.endswith('/'):
                p = p[:-1]
            front.append((method, p, rel))"""

    if OLD_BLOCK in s:
        s = s.replace(OLD_BLOCK, NEW_BLOCK, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('已支持字符串拼接路径')
    else:
        print('主体锚点不匹配')
else:
    print('CALL_RE 锚点不匹配')
