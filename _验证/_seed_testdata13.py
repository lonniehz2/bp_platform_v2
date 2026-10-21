# -*- coding: utf-8 -*-
"""保障档案建档 → 收入档位重算 → 重新审核 → 轮候 → 摇号"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
PERSONS = D['persons']
APPS = D.get('applications', [])
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

# ---------- 1) 建档 + 收入档位 ----------
print('— 保障档案 —')
for i, pid in enumerate(PERSONS, 1):
    r = call('POST', '/api/v1/guarantee-profiles', {
        'personId': pid, 'securityType': 'PUBLIC', 'familySize': 2,
        'familyType': 'COUPLE', 'monthlyIncome': 3000,
        'assetDeclare': 0, 'hasHouse': 0, 'houseCount': 0, 'hasVehicle': 0})
    print('  %s 建档 人员%s %s' % ('✓' if ok(r) else '✗', pid,
                                 str(r.get('message'))[:46]))
    r2 = call('POST', '/api/v1/guarantee-profiles/person/%s/recalc-income' % pid,
              {'lowLine': 1200, 'lowIncomeLine': 2400, 'middleLowLine': 4000})
    print('    收入档位 → %s' % (r2.get('data') or {}).get('incomeLevelAfter'))

# ---------- 2) 重新审核（此前因档案缺失被拦）----------
print('\n— 重新审核 —')
approved = []
for a in APPS:
    r = call('POST', '/api/v1/applications/%s/review' % a['id'], {
        'stage': 'FINAL', 'result': 'PASS', 'opinion': '档案齐全，通过'})
    st = (r.get('data') or {}).get('applicationStatus')
    print('  %s 申请%s → %s %s' % ('✓' if ok(r) else '✗', a['id'], r.get('code'),
                                  st or str(r.get('message'))[:44]))
    if ok(r):
        approved.append(a)

# ---------- 3) 轮候 ----------
print('\n— 轮候 —')
w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=10')
total = (w.get('data') or {}).get('total') or 0
print('  队列 %s 条' % total)
if total == 0:
    for a in approved:
        r = call('POST', '/api/v1/allocation/waiting', {
            'personId': a['personId'], 'orgId': D['orgId'],
            'securityType': 'PUBLIC', 'priorityScore': 0})
        print('  %s 入队 人员%s %s' % ('✓' if ok(r) else '✗', a['personId'],
                                      str(r.get('message'))[:44]))
    w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=10')
    print('  入队后队列：%s 条' % ((w.get('data') or {}).get('total') or 0))

# ---------- 4) 摇号 ----------
print('\n— 摇号 —')
if BATCH:
    r = call('POST', '/api/v1/allocation/lottery', {'batchId': BATCH, 'seed': '20261020'})
    print('  %s → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                           str(r.get('data') or r.get('message'))[:110]))
    res = call('GET', '/api/v1/allocation/lottery/%s' % BATCH)
    rows = res.get('data') or []
    print('  结果 %d 条' % len(rows))
    for x in rows[:5]:
        print('    %s 人员%s 总分%s 名次%s 类型%s'
              % (x.get('queueId'), x.get('personId'), x.get('totalScore'),
                 x.get('rankNo'), x.get('resultType')))

al = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10')
print('\n配租单 %s 条' % ((al.get('data') or {}).get('total') or 0))
for x in ((al.get('data') or {}).get('rows') or [])[:5]:
    print('  %s 人员%s 房源%s 状态%s 锁定剩余%s h'
          % (x.get('allocationNo'), x.get('personId'), x.get('houseId'),
             x.get('allocationStatus'), x.get('lockRemainHours')))
