# -*- coding: utf-8 -*-
"""回归：批次人数、结果总分/未中签、自动公示、日房态、入住信息、删除校验、黑名单、续签。"""
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
        with urllib.request.urlopen(req, timeout=60) as r:
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
                           read_timeout=90)


# 1) 已摇号批次参与人数 = 结果数
st, r = call('/allocation/batches?pageNum=1&pageSize=50')
done = [b for b in r['data']['rows'] if b['batchStatus'] in
        ('LOTTERY_DONE', 'SELECTING', 'ALLOCATED')]
c = db(); cur = c.cursor()
bad = []
for b in done[:10]:
    cur.execute('select count(*) from bp_biz_lottery_result where batch_id=%s', (b['id'],))
    n = cur.fetchone()[0]
    if int(b['applicantCount'] or 0) != int(n):
        bad.append((b['batchNo'], b['applicantCount'], n))
print('1 已摇号批次人数:', '✔' if not bad else ('✘ ' + str(bad)))

# 2) 结果总分与“未中签”文案
if done:
    st, r = call('/allocation/lottery/' + str(done[0]['id']))
    rows = r.get('data') or []
    has_score = all(row.get('totalScore') is not None for row in rows)
    labels = {row.get('resultType'): row.get('resultTypeLabel') for row in rows}
    print('2 结果:', len(rows), '总分齐全', has_score, '标签', labels)

# 3) 自动公示：找未摇号批次摇一次
c = db(); cur = c.cursor()
cur.execute("""select b.id from bp_biz_batch b
               where b.batch_status in ('PUBLISHED','SIGNUP')
                 and (select count(*) from bp_biz_waiting_queue w
                      where w.queue_status='WAITING' and w.security_type=b.security_type
                        and (b.org_id is null or w.org_id=b.org_id)) > 0
                 and (select count(*) from bp_biz_batch_house h where h.batch_id=b.id) > 0
               order by b.id desc limit 1""")
row = cur.fetchone()
c.close()
if row:
    st, r = call('/allocation/lottery', 'POST', {'batchId': row[0], 'seed': 'auto-publicity'})
    c = db(); cur = c.cursor()
    cur.execute("select publicity_no,start_date,end_date,batch_id from bp_biz_publicity where batch_id=%s", (row[0],))
    pb = cur.fetchall()
    c.close()
    print('3 摇号自动公示:', st, pb)

# 11) 日房态合同占用
c = db(); cur = c.cursor()
cur.execute("""select house_id, lease_start, lease_end, tenant_id from bp_biz_contract
               where contract_status in ('EFFECTIVE','RENEWING','SIGNING') and is_deleted=0 limit 1""")
row = cur.fetchone()
c.close()
if row:
    st, r = call('/house-calendar/' + str(row[0]) + '?month=' + str(row[2])[:7])
    cells = r.get('data') or []
    leased = [x for x in cells if x.get('dayStatus') == 'LEASED']
    print('11 日房态:', st, 'LEASED 天数', len(leased))
    st, r = call('/houses/' + str(row[0]) + '/occupancy')
    d = r.get('data') or {}
    print('12 入住信息:', st, {k: d.get(k) for k in ('occupied', 'tenantName', 'tenantCount', 'cohabitantCount')})

# 8) 删除已实名人员
c = db(); cur = c.cursor()
cur.execute("""select id from bp_person where verify_status not in ('NONE','UNVERIFIED','FAILED')
               and verify_status is not null and is_deleted=0 limit 1""")
row = cur.fetchone()
c.close()
if row:
    st, r = call('/persons/' + str(row[0]), 'DELETE')
    print('8 删除已核验人员:', st, r.get('message'))

# 9) 黑名单人员申请
c = db(); cur = c.cursor()
cur.execute("select id from bp_person where person_status='BLACKLIST' and is_deleted=0 limit 1")
row = cur.fetchone()
c.close()
if row:
    st, r = call('/applications', 'POST', {
        'orgId': 371689292805836800, 'personId': row[0], 'securityType': 'PUBLIC',
        'securityMode': 'HOUSE', 'applyChannel': 'OFFLINE', 'familySize': 2,
        'declaredIncome': 3000, 'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1})
    print('9 黑名单申请:', st, r.get('message'))
    st, r = call('/allocation/waiting', 'POST', {
        'personId': row[0], 'orgId': 371689292805836800, 'securityType': 'PUBLIC',
        'priorityScore': 1})
    print('10 黑名单入队:', st, r.get('message'))
