# -*- coding: utf-8 -*-
"""查询待审申请 → 审核通过 → 轮候 → 摇号 → 配租单"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
BATCH = D.get('batchId')


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=90) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__, 'message': str(e)}


def ok(r):
    return r.get('code') == 'BP00000'


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

# ---------- 1) 取所有申请单 ----------
r = call('GET', '/api/v1/applications?pageNum=1&pageSize=50')
apps = (r.get('data') or {}).get('rows') or []
print('申请单 %d 条：%s' % (len(apps),
      ', '.join('%s' % a.get('applicationStatus') for a in apps[:6])))

# ---------- 2) 逐个审核通过 ----------
print('\n— 审核 —')
approved = []
for a in apps:
    st = a.get('applicationStatus')
    if st in ('APPROVED',):
        approved.append(a)
        continue
    if st in ('DRAFT', 'SUBMITTED'):
        call('POST', '/api/v1/applications/%s/accept' % a['id'])
    r2 = call('POST', '/api/v1/applications/%s/review' % a['id'], {
        'stage': 'FINAL', 'result': 'PASS', 'opinion': '档案齐全，自动通过'})
    good = ok(r2)
    print('  %s 申请%s (%s) → %s %s'
          % ('✓' if good else '✗', a['id'], st, r2.get('code'),
             (r2.get('data') or {}).get('applicationStatus')
             or str(r2.get('message'))[:44]))
    if good:
        approved.append(r2.get('data') or a)

# ---------- 3) 轮候 ----------
print('\n— 轮候 —')
w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=10')
total = (w.get('data') or {}).get('total') or 0
print('  队列 %s 条' % total)
if total == 0:
    for a in approved[:3]:
        rr = call('POST', '/api/v1/allocation/waiting', {
            'personId': a.get('personId'), 'orgId': D['orgId'],
            'applicationId': a.get('id'), 'securityType': 'PUBLIC',
            'priorityScore': 0})
        print('  %s 入队 人员%s %s' % ('✓' if ok(rr) else '✗', a.get('personId'),
                                      str(rr.get('message'))[:40]))
    w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=10')
    total = (w.get('data') or {}).get('total') or 0
    print('  入队后 %s 条' % total)

# ---------- 4) 摇号 ----------
print('\n— 摇号 —')
if BATCH and total:
    r = call('POST', '/api/v1/allocation/lottery', {'batchId': BATCH, 'seed': '20261020'})
    print('  %s → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                           str(r.get('data') or r.get('message'))[:110]))
    res = call('GET', '/api/v1/allocation/lottery/%s' % BATCH)
    rows = res.get('data') or []
    for x in rows[:5]:
        print('    %s 人员%s 总分%s 名次%s %s'
              % (x.get('queueId'), x.get('personId'), x.get('totalScore'),
                 x.get('rankNo'), x.get('resultType')))

al = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10')
print('\n配租单 %s 条' % ((al.get('data') or {}).get('total') or 0))
for x in ((al.get('data') or {}).get('rows') or [])[:5]:
    print('  %s 人员%s 房源%s %s 锁定%s h'
          % (x.get('allocationNo'), x.get('personId'), x.get('houseId'),
             x.get('allocationStatus'), x.get('lockRemainHours')))
