# -*- coding: utf-8 -*-
import json
import time
import urllib.request

import pymysql

B = 'http://192.168.31.11:8080/api/v1'
CID = 374466995221041152

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('select id,paid_amount,deduct_amount,refund_amount,balance_amount,deposit_status '
            'from bp_fin_deposit where contract_id=%s order by id desc limit 1', (CID,))
dep = cur.fetchone()
if dep:
    did = dep[0]
    cur.execute('update bp_fin_deposit set paid_amount=1000, deduct_amount=0, refund_amount=0, '
                'balance_amount=1000, deposit_status="HELD" where id=%s', (did,))
else:
    did = int(time.time() * 1000) * 1000
    cur.execute("""insert into bp_fin_deposit
      (id,tenant_id,contract_id,person_id,deposit_amount,paid_amount,deduct_amount,
       refund_amount,balance_amount,deposit_status,is_exempt,over_cap_flag,create_time,update_time,org_id)
      select %s,'350600',id,lessee_person_id,1000,1000,0,0,1000,'HELD',0,0,now(3),now(3),org_id
      from bp_biz_contract where id=%s""", (did, CID))
print('deposit', did)

r = urllib.request.Request(B + '/auth/login', data=json.dumps(
    {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
tok = json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']
H = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok, 'X-Tenant-Id': '350600'}
req = urllib.request.Request(B + '/fin/refunds', data=json.dumps({
    'contractId': CID, 'refundAmount': 300, 'refundType': 'DEPOSIT',
    'refundChannel': 'ORIGINAL', 'refundReason': '联调测试'
}).encode(), method='POST', headers=H)
ref = json.loads(urllib.request.urlopen(req, timeout=30).read())['data']
rid = ref['id']
print('refund', rid, ref['refundStatus'])
cur.execute('select refund_amount,balance_amount,deposit_status from bp_fin_deposit where id=%s', (did,))
print('创建后', cur.fetchone())

req = urllib.request.Request(B + '/fin/refunds/%s/reject' % rid,
                             data=json.dumps({'approveById': None, 'reason': '测试驳回'}).encode(),
                             method='POST', headers=H)
print('驳回', json.loads(urllib.request.urlopen(req, timeout=30).read())['data']['refundStatus'])
cur.execute('select refund_amount,balance_amount,deposit_status from bp_fin_deposit where id=%s', (did,))
print('驳回后', cur.fetchone())

cur.execute('delete from bp_fin_refund where id=%s', (rid,))
cur.execute('delete from bp_fin_deposit where id=%s', (did,))
print('cleaned')
c.close()
