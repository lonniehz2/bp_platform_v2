# -*- coding: utf-8 -*-
import json
import time
import urllib.request

import pymysql

B = 'http://192.168.31.11:8080/api/v1'
ELEC = 371722116640411648

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
# 楼栋总表（仅分析）
pid = int(time.time() * 1000) * 1000 + 30
cur.execute("""insert into bp_fin_meter_point
 (id,tenant_id,space_id,fee_item_id,meter_scope,allocation_basis,meter_name,bed_capacity,status,create_time,update_time)
 values (%s,'350600',NULL,%s,'BUILDING','PERSON_DAYS','M2楼栋电总表',NULL,'ENABLED',now(3),now(3))""",
            (pid, ELEC))
for rd, t in [(1000, '2026-10-01 00:00:00'), (1320, '2026-10-31 23:59:00')]:
    cur.execute("""insert into bp_fin_meter_point_reading
     (id,tenant_id,meter_point_id,reading,read_time,source,create_time)
     values (%s,'350600',%s,%s,%s,'MANUAL',now(3))""",
                (int(time.time() * 1000) * 1000 + (40 if rd == 1000 else 41), pid, rd, t))
print('building meter', pid)

# 滞纳金测试账单
bid = int(time.time() * 1000) * 1000 + 50
cur.execute("""insert into bp_fin_bill
 (id,tenant_id,bill_no,org_id,contract_id,fee_item_id,bill_period,period_start,period_end,
  bill_amount,discount_amount,late_fee,paid_amount,waived_amount,payable_amount,due_date,
  bill_status,overdue_days,generate_type,is_deleted,create_time)
 values (%s,'350600',%s,374380703720280064,374466995221041152,%s,'2026-09',
  '2026-09-01','2026-09-30',1000,0,0,0,0,1000,'2026-09-01','UNPAID',0,'MANUAL',0,now(3))""",
            (bid, 'LATE' + str(bid), ELEC))
print('late bill', bid)
c.close()


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(B + path, data=data, method=method, headers=h)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


tok = call('/auth/login', 'POST',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']
d = call('/fin/energy-analysis/monthly?period=2026-10&feeItemId=%s' % ELEC, token=tok)['data']
print('energy', d)

r = call('/fin/late-fees/run?date=2026-10-10&billId=%s' % bid, 'POST', {}, tok)
print('late count', r['data'])
c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('select bill_amount,late_fee,late_fee_days,payable_amount,bill_status from bp_fin_bill where id=%s', (bid,))
print('bill', cur.fetchone())
c.close()
