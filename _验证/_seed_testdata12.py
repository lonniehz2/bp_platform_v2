# -*- coding: utf-8 -*-
"""补实名认证 → 申请 → 受理 → 审核 → 轮候 → 批次(含 batchType) → 摇号 → 配租"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG, PERSONS = D['orgId'], D['persons']
HOUSES = [h for h in D.get('houses', []) if h]


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

# ---------- 1) 实名认证（faceResult=1 同一人, citizenResult=1 一致）----------
print('— 实名认证 —')
for i, pid in enumerate(PERSONS, 1):
    r = call('POST', '/api/v1/verify-records', {
        'personId': pid, 'verifyType': 'FACE_COMPARE', 'userName': '测试租户%d' % i,
        'commandId': 'CMD%d' % i, 'responseCode': '100', 'resultCode': '1',
        'faceScore': 92.5, 'faceResult': '1', 'citizenResult': '1',
        'rawResponse': '{"mock":true}'})
    print('  %s 人员%s → verifyPass=%s'
          % ('✓' if ok(r) else '✗', pid, (r.get('data') or {}).get('verifyPass')))

# ---------- 2) 申请 → 受理 → 审核通过 ----------
print('\n— 申请与审核 —')
apps = []
for i, pid in enumerate(PERSONS[:3], 1):
    r = call('POST', '/api/v1/applications', {
        'orgId': ORG, 'personId': pid, 'securityType': 'PUBLIC',
        'securityMode': 'HOUSE', 'applyChannel': 'OFFLINE', 'familySize': 2,
        'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1, 'declaredIncome': 3000})
    aid = (r.get('data') or {}).get('id')
    print('  %s 申请%d → %s %s' % ('✓' if ok(r) else '✗', i, aid,
                                  str(r.get('message'))[:46]))
    if not aid:
        continue
    call('POST', '/api/v1/applications/%s/accept' % aid)
    r3 = call('POST', '/api/v1/applications/%s/review' % aid, {
        'stage': 'FINAL', 'result': 'PASS', 'opinion': '自动通过'})
    st = (r3.get('data') or {}).get('applicationStatus')
    print('    审核 → %s %s' % (r3.get('code'), st or str(r3.get('message'))[:40]))
    if ok(r3):
        apps.append({'id': aid, 'personId': pid})

# ---------- 3) 轮候 ----------
print('\n— 轮候 —')
w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=10')
print('  队列 %s 条' % (w.get('data') or {}).get('total'))
if not ((w.get('data') or {}).get('total') or 0) and apps:
    r = call('POST', '/api/v1/allocation/waiting', {
        'personId': apps[0]['personId'], 'orgId': ORG,
        'securityType': 'PUBLIC', 'priorityScore': 0})
    print('  入队：%s %s' % (r.get('code'), str(r.get('message'))[:50]))

# ---------- 4) 批次（batchType=LOTTERY）----------
print('\n— 配租批次 —')
r = call('POST', '/api/v1/allocation/batches', {
    'batchName': '测试配租批次' + str(int(time.time()))[-4:], 'orgId': ORG,
    'securityType': 'PUBLIC', 'batchType': 'LOTTERY',
    'houseIds': HOUSES[:3], 'remark': '自动生成'})
batch_id = (r.get('data') or {}).get('id')
print('  %s 建批次 → %s %s' % ('✓' if ok(r) else '✗', batch_id,
                              str(r.get('message'))[:60]))

if batch_id:
    r = call('POST', '/api/v1/allocation/batches/%s/status' % batch_id,
             {'batchStatus': 'PUBLISHED'})
    print('  %s 发布 → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                                str(r.get('message'))[:40]))
    r = call('POST', '/api/v1/allocation/lottery',
             {'batchId': batch_id, 'seed': '20261020'})
    print('  %s 摇号 → %s %s' % ('✓' if ok(r) else '✗', r.get('code'),
                                str(r.get('data') or r.get('message'))[:100]))
    res = call('GET', '/api/v1/allocation/lottery/%s' % batch_id)
    print('  摇号结果：%s 条' % len(res.get('data') or []))

al = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10')
print('\n  配租单 %s 条' % (al.get('data') or {}).get('total'))
for x in ((al.get('data') or {}).get('rows') or [])[:3]:
    print('    %s 人员%s 房源%s 状态%s' % (x.get('allocationNo'), x.get('personId'),
                                        x.get('houseId'), x.get('allocationStatus')))

D['batchId'] = batch_id
D['applications'] = apps
json.dump(D, open(r'D:\Work\业务平台开发\_验证\_test_data.json', 'w',
                  encoding='utf-8'), ensure_ascii=False, indent=1)
