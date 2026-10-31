# -*- coding: utf-8 -*-
import json
import urllib.request

import pymysql

B = 'http://192.168.31.11:8080/api/v1'
c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('select id, contract_id, house_id from bp_biz_termination order by id desc limit 5')
rows = cur.fetchall()
print('terminations', rows)
tid, cid, hid = rows[0]
cur.execute("""select coalesce(sum(bill_amount - discount_amount + late_fee - paid_amount
                - waived_amount),0) from bp_fin_bill where contract_id=%s and bill_status in
                ('UNPAID','PARTIAL','OVERDUE') and is_deleted=0""", (cid,))
expect = cur.fetchone()[0]
cur.execute('select balance_amount from bp_fin_deposit where contract_id=%s order by id desc limit 1', (cid,))
dep = cur.fetchone()
print('contract', cid, 'expected arrears', expect, 'deposit ledger', dep)

r = urllib.request.Request(B + '/auth/login', data=json.dumps(
    {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
tok = json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']
req = urllib.request.Request(B + '/terminations/%s/settle-preview' % tid,
                             headers={'Authorization': 'Bearer ' + tok, 'X-Tenant-Id': '350600'})
print('preview', json.loads(urllib.request.urlopen(req, timeout=30).read())['data'])
c.close()
