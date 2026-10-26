# -*- coding: utf-8 -*-
"""数据健康：新增「悬空引用」检查，避免测试残留（id=1）再次污染列表与显示层。

挂在 _check_data_health.py 里，随流水线执行。
"""
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, '_check_data_health.py')
s = io.open(P, encoding='utf-8').read()

if '悬空引用' in s:
    print('已存在悬空引用检查')
else:
    ANCHOR = "def main("
    BLOCK = '''DANGLING_SQL = [
    ('合同→房源', "select count(*) from bp_biz_contract c "
                 "left join bp_asset_house h on h.id=c.house_id "
                 "where c.house_id is not null and h.id is null"),
    ('合同→组织', "select count(*) from bp_biz_contract c "
                 "left join bp_iam_org o on o.id=c.org_id "
                 "where c.org_id is not null and o.id is null"),
    ('合同→承租人', "select count(*) from bp_biz_contract c "
                   "left join bp_person p on p.id=c.lessee_person_id "
                   "where c.lessee_person_id is not null and p.id is null"),
    ('申请→组织', "select count(*) from bp_biz_application a "
                 "left join bp_iam_org o on o.id=a.org_id "
                 "where a.org_id is not null and o.id is null"),
    ('换房→原合同', "select count(*) from bp_biz_exchange e "
                   "left join bp_biz_contract c on c.id=e.old_contract_id "
                   "where e.old_contract_id is not null and c.id is null"),
    ('账单→合同', "select count(*) from bp_fin_bill b "
                 "left join bp_biz_contract c on c.id=b.contract_id "
                 "where b.contract_id is not null and c.id is null"),
]


def check_dangling(cur):
    """悬空引用：外键指向不存在的记录（多为测试脚本用 id=1 造数残留）。"""
    bad = []
    for label, sql in DANGLING_SQL:
        try:
            cur.execute(sql)
            n = cur.fetchone()[0]
        except Exception:
            continue
        if n:
            bad.append('%s %d 条' % (label, n))
    return bad


'''
    if ANCHOR in s:
        s = s.replace(ANCHOR, BLOCK + ANCHOR, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('已加入 check_dangling 定义')
    else:
        print('未找到 main()')
