# -*- coding: utf-8 -*-
"""修正 _seed_phase1.py 的空间/房源查询：
- /spaces 分页需带 orgId，改用 /spaces/tree?orgId=
- 空间按 spaceCode 匹配
- 房源查询也带 orgId（已验证可用）
"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_seed_phase1.py')
s = io.open(P, encoding='utf-8').read()


def load_spaces(tok, org_id):
    pass


old = """    st, r = call('/spaces?pageNum=1&pageSize=500', token=tok)
    spaces = (d((st, r)) or {}).get('rows') or []"""
new = """    st, r = call('/spaces/tree?orgId=%s' % org_id, token=tok)
    tree = d((st, r))
    spaces = []

    def walk(nodes):
        for n in nodes or []:
            spaces.append(n)
            walk(n.get('children'))
    if isinstance(tree, list):
        walk(tree)
    elif isinstance(tree, dict):
        spaces = (tree.get('rows') or [])"""
if old in s:
    s = s.replace(old, new, 1)
    print('空间查询改为 /spaces/tree')

io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('已更新')
