# -*- coding: utf-8 -*-
import json
import time
import urllib.request

import pymysql

B = 'http://192.168.31.11:8080/api/v1'
OLD = 1793419865030000  # M2 测试合同 A

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=120)
cur = c.cursor()
cur.execute('select id,house_id,org_id,lessee_person_id,lessee_name,space_id from bp_biz_contract where id=%s', (OLD,))
oid, ohouse, org, person, name, space = cur.fetchone()
cur.execute("select id from bp_asset_house where house_status='VACANT' and is_deleted=0 limit 1")
newhouse = cur.fetchone()[0]
print('old', oid, ohouse, 'new house', newhouse)

# 旧合同押金 1000
dep = int(time.time() * 1000) * 1000 + 60
cur.execute('select id from bp_fin_deposit where contract_id=%s', (OLD,))
if cur.fetchone():
    cur.execute('update bp_fin_deposit set paid_amount=1000,deduct_amount=0,refund_amount=0,balance_amount=1000,deposit_status="HELD" where contract_id=%s', (OLD,))
else:
    cur.execute("""insert into bp_fin_deposit
     (id,tenant_id,contract_id,person_id,deposit_amount,paid_amount,deduct_amount,refund_amount,
      balance_amount,deposit_status,is_exempt,over_cap_flag,create_time,update_time,org_id,source_type)
     values (%s,'350600',%s,%s,1000,1000,0,0,1000,'HELD',0,0,now(3),now(3),%s,'NEW')""",
                (dep, OLD, person, org))

# 复制历史换房单，改为测试数据
cur.execute('select * from bp_biz_exchange order by id desc limit 1')
cols = [d[0] for d in cur.description]
base = dict(zip(cols, cur.fetchone()))
nid = int(time.time() * 1000) * 1000 + 61
row = dict(base)
row['id'] = nid
row['exchange_no'] = 'M3EX' + str(nid)[-6:]
row['old_contract_id'] = OLD
row['old_house_id'] = ohouse
row['new_house_id'] = newhouse
row['person_id'] = person
row['person_name'] = name
row['exchange_status'] = 'APPROVED'
row['org_id'] = org
for k in ('new_contract_id', 'grant_migrated'):
    if k in row:
        row[k] = 0 if k == 'grant_migrated' else None
ph = ','.join(['%s'] * len(cols))
cur.execute('insert into bp_biz_exchange (%s) values (%s)' % (','.join(cols), ph),
            [row[k] for k in cols])
print('exchange', nid)
c.close()

r = urllib.request.Request(B + '/auth/login', data=json.dumps(
    {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
tok = json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']
req = urllib.request.Request(B + '/exchanges/%s/complete' % nid, data=b'{}', method='POST',
                             headers={'Content-Type': 'application/json',
                                      'Authorization': 'Bearer ' + tok, 'X-Tenant-Id': '350600'})
try:
    print('complete', urllib.request.urlopen(req, timeout=60).read().decode()[:200])
except urllib.error.HTTPError as e:
    print('complete', e.code, e.read().decode()[:200])

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('select id,contract_id,balance_amount,deposit_status,source_type from bp_fin_deposit where contract_id in (%s,%s) order by id', (OLD, row.get('new_contract_id') or 0))
print('deposits', cur.fetchall())
cur.execute('select * from bp_fin_deposit_transfer where exchange_id=%s', (nid,))
print('transfer row', cur.fetchall())
c.close()
