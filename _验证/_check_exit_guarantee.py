# -*- coding: utf-8 -*-
"""退出保障联动与资格判定校验。"""
import json
import urllib.error
import urllib.request

import pymysql

B = 'http://192.168.31.11:8080/api/v1'
H = {'X-Tenant-Id': '350600'}


def login():
    r = urllib.request.Request(B + '/auth/login',
                               data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                                                'password': 'admin123'}).encode(),
                               method='POST',
                               headers={'Content-Type': 'application/json',
                                        'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']


H['Authorization'] = 'Bearer ' + login()


def call(path, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    req = urllib.request.Request(B + path, data=data, method=method,
                                 headers={**H, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def db():
    return pymysql.connect(host='192.168.31.153', port=33306, user='root',
                           password='5677@Mysql', database='bp_platform',
                           charset='utf8mb4', autocommit=True, connect_timeout=20,
                           read_timeout=60)


PERSON = 370832686538952704

st, r = call(f'/guarantee-profiles/person/{PERSON}')
print('档案状态:', st, (r.get('data') or {}).get('profileStatus'))

st, r = call(f'/guarantee-profiles/person/{PERSON}/exit', 'POST',
             {'exitDate': '2026-10-28', 'exitReason': '回归：退出保障联动验证'})
print('退出保障:', st, (r.get('data') or {}).get('profileStatus'), r.get('message') or '')

c = db(); cur = c.cursor()
cur.execute("""select queue_status from bp_biz_waiting_queue where person_id=%s""", (PERSON,))
print('退出后轮候状态:', [x[0] for x in cur.fetchall()])

cur.execute("""select id,application_id,org_id,security_type from bp_biz_waiting_queue
               where person_id=%s limit 1""", (PERSON,))
row = cur.fetchone()
c.close()

if row:
    st, r = call('/allocation/waiting', 'POST', {
        'personId': PERSON, 'applicationId': row[1], 'orgId': row[2],
        'securityType': row[3], 'priorityScore': 1})
    print('退出后再入队:', st, r.get('message'))

st, r = call('/applications', 'POST', {
    'orgId': 371689292805836800, 'personId': PERSON, 'securityType': 'PUBLIC',
    'securityMode': 'HOUSE', 'applyChannel': 'OFFLINE', 'familySize': 2,
    'declaredIncome': 3000, 'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1})
print('退出后新申请:', st, r.get('message'))

st, r = call(f'/guarantee-profiles/person/{PERSON}/qualify', 'POST')
print('退出后再资格判定:', st, r.get('message'))

# 资格判定校验：找一个 NORMAL 收入的档案
c = db(); cur = c.cursor()
cur.execute("""select person_id from bp_person_guarantee_profile
               where income_level='NORMAL' and profile_status<>'EXITED' limit 1""")
row = cur.fetchone()
c.close()
if row:
    st, r = call(f'/guarantee-profiles/person/{row[0]}/qualify', 'POST')
    print('普通收入资格判定:', st, r.get('message'))
else:
    print('普通收入资格判定: 无样本')
