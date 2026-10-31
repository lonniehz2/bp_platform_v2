# -*- coding: utf-8 -*-
import json
import time
import urllib.request

import pymysql

B = 'http://192.168.31.11:8080/api/v1'
CID = 374466995221041152
ITEM = 374371142242275328


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(B + path, data=data, method=method, headers=h)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


tok = call('/auth/login', 'POST',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']

# 1) 生成一张 2026-12 租金账单
gen = call('/fin/bills/generate', 'POST', {
    'feeItemId': ITEM, 'periodStart': '2026-12-01', 'periodEnd': '2026-12-31',
    'billPeriod': '2026-12', 'contractIds': [CID], 'dryRun': False
}, tok)['data']
bill_id = gen['items'][0]['billId']
print('账单生成', bill_id, gen['items'][0]['amount'])

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('select org_id, lessee_person_id, lessee_name from bp_biz_contract where id=%s', (CID,))
org, person, name = cur.fetchone()

# 2) 造一笔待发放的补贴（抵扣租金）
sid = int(time.time() * 1000) * 1000
cur.execute("""insert into bp_fin_subsidy_record
 (id,tenant_id,record_no,contract_id,person_id,person_name,org_id,subsidy_period,
  subsidy_amount,paid_amount,pay_mode,record_status,create_by,create_time,update_time)
 values (%s,'350600',%s,%s,%s,%s,%s,'2026-12',200,0,'OFFSET','PENDING','test',now(3),now(3))""",
            (sid, 'FS' + str(sid), CID, person, name, org))
print('补贴记录', sid)

# 3) 确认发放
res = call('/fin/subsidies/records/%s/confirm' % sid, 'POST', {'paidAmount': 200}, tok)
print('发放', res['data']['recordStatus'], res['data']['paidAmount'])

# 4) 账单变化
cur.execute('select bill_amount,waived_amount,payable_amount,bill_status from bp_fin_bill where id=%s', (bill_id,))
print('账单 应收/减免/待缴/状态 =', cur.fetchone())

# 5) 清理测试数据（账单、补贴、补贴支出流水）
cur.execute('delete from bp_fin_bill where id=%s', (bill_id,))
cur.execute('delete from bp_fin_subsidy_record where id=%s', (sid,))
cur.execute('delete from bp_fin_cashflow where biz_type=%s and biz_id=%s', ('SUBSIDY', sid))
print('已清理')
c.close()
