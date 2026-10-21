# -*- coding: utf-8 -*-
"""占用联动全链路验证：建合同 → 生效(占房) → 终止(退房)

用法：python _diag_occupy_cycle.py [--keep]
        --keep  结束后不清理，便于查库
"""
import json
import sys
import urllib.request

import pymysql

BASE = 'http://192.168.31.11:8080'
KEEP = '--keep' in sys.argv


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Tenant-Id', '350600')
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {'code': 'HTTP%d' % e.code, 'message': e.read().decode()[:200]}


tok = call('/api/v1/auth/login', 'POST',
           {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})['data']['token']

houses = call('/api/v1/houses?pageNum=1&pageSize=5&houseStatus=VACANT', token=tok)['data']['rows']
persons = call('/api/v1/persons?pageNum=1&pageSize=1', token=tok)['data']['rows']
h, p = houses[0], persons[0]
print('房源 %s（%s，上限 %s 人）' % (h['id'], h['houseCode'], h.get('maxCapacity')))
print('人员 %s' % p['personName'])

created = call('/api/v1/contracts', 'POST', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': h['orgId'], 'lessorOrgId': h.get('ownerOrgId') or h['orgId'],
    'lesseePersonId': p['id'], 'lesseeName': p['personName'], 'lesseePhone': '13900003333',
    'houseId': h['id'], 'spaceId': h['spaceId'], 'houseAddress': h['houseName'],
    'leaseStart': '2026-11-01', 'leaseEnd': '2027-10-31',
    'rentPrice': 20, 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': 1000,
    'depositAmount': 1000, 'payCycle': 'MONTH', 'payDay': 5,
}, tok)
cid = (created.get('data') or {}).get('id')
cno = (created.get('data') or {}).get('contractNo')
print('\n① 建合同 %s → %s' % (cno, created.get('code')))


def house_state():
    d = call('/api/v1/houses/' + str(h['id']), token=tok)['data']
    return d.get('houseStatus'), d.get('currentCapacity')


def occ_rows():
    c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                        password='5677@Mysql', database='bp_platform', charset='utf8mb4')
    cur = c.cursor()
    cur.execute("select status, start_date, end_date from bp_asset_space_occupancy where source_id=%s", (cid,))
    rows = cur.fetchall()
    c.close()
    return rows


print('   房源 %s，占用流水 %s' % (house_state(), occ_rows()))

for step, path in (('② 提交待签', 'submit-sign'), ('③ 开始签约', 'start-signing')):
    r = call('/api/v1/contracts/%s/%s' % (cid, path), 'POST',
             {'signVendor': 'OFFLINE'} if path == 'start-signing' else None, tok)
    print('%s → %s，房源 %s' % (step, r.get('code'), house_state()))

r = call('/api/v1/contracts/%s/sign' % cid, 'POST', {'signFileUrl': 'x', 'signFlowId': 'y'}, tok)
st, cap = house_state()
print('④ 签约 → %s，合同状态 %s，房源 %s，占用 %s'
      % (r.get('code'), (r.get('data') or {}).get('contractStatus'), (st, cap), occ_rows()))
ok_occupy = r.get('code') == 'BP00000' and st == 'OCCUPIED' and any(x[0] == 'ACTIVE' for x in occ_rows())

r = call('/api/v1/contracts/%s/terminate' % cid, 'POST', {'reason': '占用联动验证'}, tok)
st2, cap2 = house_state()
print('⑤ 终止 → %s，房源 %s，占用 %s' % (r.get('code'), (st2, cap2), occ_rows()))
ok_release = r.get('code') == 'BP00000' and st2 == 'VACANT' and all(x[0] == 'FINISHED' for x in occ_rows())

print('\n结论：占房 %s ｜ 退房 %s' % ('✔ 通过' if ok_occupy else '✘ 失败',
                                 '✔ 通过' if ok_release else '✘ 失败'))

if not KEEP:
    c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                        password='5677@Mysql', database='bp_platform', charset='utf8mb4')
    cur = c.cursor()
    cur.execute('delete from bp_asset_space_occupancy where source_id=%s', (cid,))
    cur.execute('delete from bp_biz_contract where id=%s', (cid,))
    cur.execute("update bp_asset_house set house_status='VACANT', current_capacity=0 where id=%s", (h['id'],))
    c.commit()
    c.close()
    print('已清理测试合同与占用，房源 %s 恢复空置' % h['id'])

sys.exit(0 if (ok_occupy and ok_release) else 1)
