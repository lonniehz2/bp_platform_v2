# -*- coding: utf-8 -*-
"""回归：配置不新增、轮候改分、重复申请、批次房源重复入池、参与人数实时。"""
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


TOKEN = login()
H['Authorization'] = 'Bearer ' + TOKEN


def call(path, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    req = urllib.request.Request(B + path, data=data, method=method,
                                 headers={**H, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def db():
    return pymysql.connect(host='192.168.31.153', port=33306, user='root',
                           password='5677@Mysql', database='bp_platform',
                           charset='utf8mb4', autocommit=True, connect_timeout=20,
                           read_timeout=60)


# ---------- A. 系统参数：修改不新增 ----------
key = 'biz.publicity.allocation.minDays'
c = db(); cur = c.cursor()
cur.execute('select count(*) from bp_sys_config where config_key=%s', (key,))
before = cur.fetchone()[0]
st, r = call('/sys/configs', 'POST', {'key': key, 'value': '7'})
cur.execute('select count(*) from bp_sys_config where config_key=%s', (key,))
after = cur.fetchone()[0]
print('A 配置修改:', st, '行数', before, '->', after, '✔' if before == after else '✘')
c.close()

# ---------- B. 轮候重复入队 => 更新附加分 ----------
st, r = call('/allocation/waiting?pageNum=1&pageSize=50')
rows = r['data']['rows']
target = next((x for x in rows if x['applicationId'] and x['orgId']
               and x['queueStatus'] in ('WAITING', 'WON')), None)
if target:
    newp = float(target['priorityScore'] or 0) + 3
    st2, r2 = call('/allocation/waiting', 'POST', {
        'personId': target['personId'], 'applicationId': target['applicationId'],
        'orgId': target['orgId'], 'securityType': target['securityType'],
        'priorityScore': newp})
    d = r2.get('data') or {}
    print('B 轮候改分:', st2, 'id', d.get('id'), 'priority', d.get('priorityScore'),
          '✔' if st2 == 200 and float(d.get('priorityScore') or -1) == newp else '✘')
else:
    print('B 轮候改分: 无可用样本')

# ---------- C. 同组织重复申请 ----------
st, r = call('/applications?pageNum=1&pageSize=50')
apps = r['data']['rows']
act = next((a for a in apps if a['applicationStatus'] in
            ('SUBMITTED', 'ACCEPTED', 'REVIEWING', 'SUPPLEMENT') and a.get('orgId')), None)
if act:
    st3, r3 = call('/applications', 'POST', {
        'orgId': act['orgId'], 'personId': act['personId'],
        'securityType': act.get('securityType') or 'PUBLIC',
        'securityMode': 'HOUSE', 'applyChannel': 'OFFLINE',
        'familySize': 2, 'declaredIncome': 3000,
        'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1})
    print('C 重复申请:', st3, r3.get('message'), '✔' if st3 != 200 else '✘')
else:
    print('C 重复申请: 无在途样本')

# ---------- D. 房源跨批次重复入池 ----------
c = db(); cur = c.cursor()
cur.execute('''select bh.house_id, b.batch_no, b.batch_status, b.id
               from bp_biz_batch_house bh join bp_biz_batch b on b.id=bh.batch_id
               where b.batch_status not in ('CLOSED','CANCELLED') limit 1''')
row = cur.fetchone()
cur.execute("""select id, batch_no from bp_biz_batch
               where batch_status not in ('CLOSED','CANCELLED') and id<>%s limit 1""", (row[3],))
other = cur.fetchone()
c.close()
if row and other:
    st4, r4 = call(f'/allocation/batches/{other[0]}/houses', 'POST', {'houseIds': [row[0]]})
    print('D 重复入池:', st4, r4.get('message'), '✔' if st4 != 200 else '✘')
else:
    print('D 重复入池: 无样本')

# ---------- E. 参与人数实时 ----------
st, r = call('/allocation/batches?pageNum=1&pageSize=20')
c = db(); cur = c.cursor()
bad = []
for b in r['data']['rows']:
    cur.execute('''select count(*) from bp_biz_waiting_queue
                   where queue_status='WAITING' and security_type=%s
                     and (%s is null or org_id=%s)''',
                (b['securityType'], b['orgId'], b['orgId']))
    live = cur.fetchone()[0]
    if int(b['applicantCount'] or 0) != int(live):
        bad.append((b['batchNo'], b['applicantCount'], live))
print('E 参与人数实时:', '✔' if not bad else ('✘ ' + str(bad[:3])))
c.close()
