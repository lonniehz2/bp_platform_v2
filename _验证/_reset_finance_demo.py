# -*- coding: utf-8 -*-
"""重置财务演示数据（清空后重建）。

清理范围：
  bp_fin_bill / bp_fin_payment / bp_fin_payment_allocate /
  bp_fin_cash_flow / bp_fin_arrears_action / bp_fin_dunning_record
抄表：把读数置回 UNBILLED（bill_id 清空），随出账重建。
保留：押金、补贴、收费项、退款（先清空退款，重建时按需生成）。
"""
import pymysql

TENANT = '350600'

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=False)
cur = conn.cursor()

# 顺序：先子表后主表
for t in ['bp_fin_payment_allocate', 'bp_fin_cash_flow', 'bp_fin_dunning_record',
          'bp_fin_arrears_action', 'bp_fin_refund', 'bp_fin_payment', 'bp_fin_bill']:
    cur.execute('delete from %s where tenant_id=%%s' % t, (TENANT,))
    print('清空 %s: %d' % (t, cur.rowcount))

cur.execute("""update bp_fin_meter_reading
               set bill_status='UNBILLED', bill_id=null
               where tenant_id=%s""", (TENANT,))
print('抄表读数重置为未出账:', cur.rowcount)

conn.commit()

cur.execute('select count(*) from bp_biz_contract where contract_status=%s and tenant_id=%s',
            ('EFFECTIVE', TENANT))
print('生效合同数:', cur.fetchone()[0])
conn.close()
