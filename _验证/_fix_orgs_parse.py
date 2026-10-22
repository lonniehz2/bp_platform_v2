# -*- coding: utf-8 -*-
"""修正 orgs 取数（返回分页对象 {rows}），并验证批次接口。"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# 1) 修正前端批次弹窗的组织加载
p = os.path.join(HERE, '..', 'frontend', 'src', 'views', 'Allocations.vue')
s = io.open(p, encoding='utf-8').read()
old = "orgOptions.value = (list || []).map((o) => ({ id: o.id, orgName: o.orgName }))"
new = ("const rows = (list && list.rows) || (Array.isArray(list) ? list : [])\n"
       "      orgOptions.value = rows.map((o) => ({ id: o.id, orgName: o.orgName }))")
if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('Allocations.vue：组织取数已修正')

# 2) 修正验证脚本
v = os.path.join(HERE, '_verify_batch_api.py')
t = io.open(v, encoding='utf-8').read()
t = t.replace("orgs = o['data']", "orgs = ((o.get('data') or {}).get('rows') or [])")
io.open(v, 'w', encoding='utf-8', newline='').write(t)
print('验证脚本已修正')
