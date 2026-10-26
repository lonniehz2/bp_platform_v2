# -*- coding: utf-8 -*-
"""修正两类口径问题：

1) 生成脚本里「已缴」账单的 payable_amount 应为 0（剩余应缴），
   与系统核销逻辑一致（核销后 payable 递减）。
2) 数据体检的「超收」判定应比较 paid 与「应收总额」，
   而不是与「剩余应缴」比较（否则已缴清的账单会被误判为超收）。
"""
import io
import os

import pymysql

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------- 1) 修正数据：已缴账单 payable=0 ----------
conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=True)
cur = conn.cursor()
cur.execute("""
    update bp_fin_bill
    set payable_amount = 0
    where bill_status = 'PAID'
      and coalesce(paid_amount,0) > 0
      and coalesce(payable_amount,0) > 0
""")
print('已缴账单 payable 归零:', cur.rowcount)

cur.execute("""
    select count(*) from bp_fin_bill
    where coalesce(paid_amount,0) > (coalesce(bill_amount,0)
          - coalesce(discount_amount,0) + coalesce(late_fee,0)
          - coalesce(waived_amount,0)) + 0.01
      and coalesce(is_deleted,0) = 0
""")
print('按应收总额判定的超收:', cur.fetchone()[0])
conn.close()

# ---------- 2) 修正体检脚本口径 ----------
P = os.path.join(HERE, '_check_data_health.py')
s = io.open(P, encoding='utf-8').read()
if '应收总额' not in s:
    OLD = '''cur.execute("""
    select id, bill_no, payable_amount, paid_amount
    from bp_fin_bill
    where coalesce(paid_amount,0) > coalesce(payable_amount,0) + 0.01
      and coalesce(is_deleted,0)=0
""")'''
    NEW = '''# 超收 = 累计已收 > 应收总额（bill_amount - 减免 + 滞纳金 - 豁免）
# 注意：不能与 payable_amount（剩余应缴）比较，否则已缴清账单会被误判
cur.execute("""
    select id, bill_no, payable_amount, paid_amount
    from bp_fin_bill
    where coalesce(paid_amount,0) > (coalesce(bill_amount,0)
          - coalesce(discount_amount,0) + coalesce(late_fee,0)
          - coalesce(waived_amount,0)) + 0.01
      and coalesce(is_deleted,0)=0
""")'''
    if OLD in s:
        s = s.replace(OLD, NEW, 1)
        io.open(P, 'w', encoding='utf-8', newline='').write(s)
        print('体检脚本已改为按应收总额判定')
    else:
        print('体检脚本锚点不匹配')
