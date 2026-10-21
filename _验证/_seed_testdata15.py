# -*- coding: utf-8 -*-
"""修正 total 为字符串导致的分支误判，完成入队 + 摇号"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
BATCH = D.get('batchId')
ORG = D['orgId']


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


def total_of(r):
    return int((r.get('data') or {}).get('total') or 0)


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

# 取已通过申请
r = call('GET', '/api/v1/applications?pageNum=1&pageSize=50&applicationStatus=APPROVED')
apps = (r.get('data') or {}).get('rows') or []
print('已通过申请 %d 条' % len(apps))

print('\n— 轮候入队 —')
w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=10')
print('  当前队列 %d 条' % total_of(w))
if total_of(w) == 0:
    for a in apps[:3]:
        rr = call('POST', '/api/v1/allocation/waiting', {
            'personId': a.get('personId'), 'orgId': ORG,
            'applicationId': a.get('id'), 'securityType': 'PUBLIC',
            'priorityScore': 0})
        print('  %s 人员%s → %s %s'
              % ('✓' if ok(rr) else '✗', a.get('personId'), rr.get('code'),
                 str(rr.get('message'))[:56]))
    w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=10')
    print('  入队后 %d 条' % total_of(w))

print('\n— 摇号 —')
if BATCH:
    r = call('POST', '/api/v1/allocation/lottery', {'batchId': BATCH, 'seed': '20261020'})
    print('  %s → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                           str(r.get('data') or r.get('message'))[:120]))
    res = call('GET', '/api/v1/allocation/lottery/%s' % BATCH)
    rows = res.get('data') or []
    print('  结果 %d 条' % len(rows))
    for x in rows[:6]:
        print('    %s 人员%s 总分%s 名次%s %s'
              % (x.get('queueId'), x.get('personId'), x.get('totalScore'),
                 x.get('rankNo'), x.get('resultType')))

al = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10')
print('\n配租单 %d 条' % total_of(al))
for x in ((al.get('data') or {}).get('rows') or [])[:5]:
    print('  %s 人员%s 房源%s %s 锁定%s h'
          % (x.get('allocationNo'), x.get('personId'), x.get('houseId'),
             x.get('allocationStatus'), x.get('lockRemainHours')))
