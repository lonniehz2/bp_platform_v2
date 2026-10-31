# -*- coding: utf-8 -*-
import json
import time
import urllib.request

import pymysql

B = 'http://192.168.31.11:8080/api/v1'
CID = 374466995221041152
ITEM = 374371142242275328
DISCOUNT_RULE = 374377485451792384

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=60)
cur = c.cursor()
cur.execute('select org_id, lessee_person_id, monthly_rent, billing_person_count, billing_bed_count '
            'from bp_biz_contract where id=%s', (CID,))
org, person, rent, pc, bc = cur.fetchone()
print('contract', org, person, rent, pc, bc)

r = urllib.request.Request(B + '/auth/login', data=json.dumps(
    {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
tok = json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']
H = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tok, 'X-Tenant-Id': '350600'}


def gen(body):
    req = urllib.request.Request(B + '/fin/bills/generate', data=json.dumps(body).encode(),
                                 method='POST', headers=H)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())['data']


base = {'feeItemId': ITEM, 'periodStart': '2026-12-01', 'periodEnd': '2026-12-31',
        'contractIds': [CID], 'dryRun': True, 'ruleMode': 'MANUAL', 'ruleId': DISCOUNT_RULE}
d = gen(base)
print('手工8折规则', d['items'][0]['amount'], d['items'][0]['explain'])

d = gen({**base, 'ruleMode': 'AUTO', 'ruleId': None})
print('自动匹配', d['items'][0]['amount'], d['items'][0]['explain'])

# 临时按人计费项目
iid = int(time.time() * 1000) * 1000
cur.execute("""insert into bp_fin_fee_item
 (id,tenant_id,item_code,item_name,item_type,calc_mode,unit_price,unit,status,is_deleted,create_time,update_time)
 values (%s,'350600',%s,'M1按人测试','RENT','BY_PERSON',10,'元/人·月','ENABLED',0,now(3),now(3))""",
            (iid, 'M1P' + str(iid)))
# 增加一名同住人
cur.execute("""insert into bp_biz_contract_cohabitant
 (id,tenant_id,contract_id,person_id,member_name,relation,is_granted,create_time)
 values (%s,'350600',%s,%s,'测试同住人','配偶',1,now(3))""",
            (iid + 1, CID, person))
d = gen({'feeItemId': iid, 'periodStart': '2026-12-01', 'periodEnd': '2026-12-31',
         'contractIds': [CID], 'dryRun': True, 'ruleMode': 'NONE'})
print('按人（含同住人）', d['items'][0]['qty'], d['items'][0]['amount'], d['items'][0]['explain'])

# 按床位 2 床
cur.execute('update bp_biz_contract set billing_bed_count=2 where id=%s', (CID,))
d = gen({'feeItemId': iid, 'periodStart': '2026-12-01', 'periodEnd': '2026-12-31',
         'contractIds': [CID], 'dryRun': True, 'ruleMode': 'NONE'})
print('按床位 2', d['items'][0]['qty'], d['items'][0]['amount'])

# 清理
cur.execute('update bp_biz_contract set billing_bed_count=%s where id=%s', (bc, CID))
cur.execute('delete from bp_biz_contract_cohabitant where id=%s', (iid + 1,))
cur.execute('delete from bp_fin_fee_item where id=%s', (iid,))
print('cleaned')
c.close()
