# -*- coding: utf-8 -*-
"""配租全链路：申请→受理→审核通过→轮候→批次→房源入池→摇号→配租→公示→签约"""
import io
import json
import os
import re
import urllib.error
import urllib.request

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG, PERSONS, HOUSES = D['orgId'], D['persons'], [h for h in D.get('houses', []) if h]


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


def dump(rel, name):
    p = os.path.join(JAVA, rel.replace('/', os.sep))
    if not os.path.exists(p):
        print('  □ %s 未找到' % name)
        return
    s = io.open(p, encoding='utf-8').read()
    m = re.search(r'record\s+' + name + r'\s*\((.*?)\)\s*\{', s, re.S)
    if m:
        print('  ■ %s' % name)
        for ln in re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split('\n'):
            t = ln.strip().rstrip(',')
            if t:
                print('     ' + t[:100])


print('=== 配租相关 DTO ===')
for rel, nm in (('biz/dto/BatchCreateCmd.java', 'BatchCreateCmd'),
                ('biz/dto/AllocationBatchCreateCmd.java', 'AllocationBatchCreateCmd')):
    dump(rel, nm)
# 控制器里内嵌 record
p = os.path.join(JAVA, 'biz', 'controller', 'AllocationController.java')
if os.path.exists(p):
    s = io.open(p, encoding='utf-8').read()
    for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
        print('  ■ %s (AllocationController) %s' % (mm.group(1),
              re.sub(r'\s+', ' ', mm.group(2))[:110]))

TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

# ---------- 1) 申请 → 受理 → 审核 ----------
print('\n— 申请与审核 —')
apps = []
for i, pid in enumerate(PERSONS[:3], 1):
    r = call('POST', '/api/v1/applications', {
        'orgId': ORG, 'personId': pid, 'securityType': 'PUBLIC',
        'securityMode': 'HOUSE', 'applyChannel': 'OFFLINE', 'familySize': 2,
        'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1,
        'declaredIncome': 3000})
    aid = (r.get('data') or {}).get('id')
    print('  %s 申请%d → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗', i,
                                  aid, str(r.get('message'))[:50]))
    if not aid:
        continue
    r2 = call('POST', '/api/v1/applications/%s/accept' % aid)
    r3 = call('POST', '/api/v1/applications/%s/review' % aid, {
        'stage': 'FINAL', 'result': 'PASS', 'opinion': '测试自动审核通过'})
    st = (r3.get('data') or {}).get('applicationStatus')
    print('    受理 %s / 审核 %s → %s'
          % (r2.get('code'), r3.get('code'), st or str(r3.get('message'))[:40]))
    if r3.get('code') == 'BP00000':
        apps.append({'id': aid, 'personId': pid})

# ---------- 2) 轮候 ----------
print('\n— 轮候 —')
w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=10')
wrows = (w.get('data') or {}).get('rows') or []
print('  轮候队列 %s 条' % (w.get('data') or {}).get('total'))
if not wrows and apps:
    r = call('POST', '/api/v1/allocation/waiting', {
        'personId': apps[0]['personId'], 'applicationId': apps[0]['id'],
        'orgId': ORG, 'securityType': 'PUBLIC'})
    print('  手动入队：%s %s' % (r.get('code'), str(r.get('message'))[:50]))

# ---------- 3) 批次 + 房源入池 ----------
print('\n— 配租批次 —')
r = call('POST', '/api/v1/allocation/batches', {
    'batchNo': 'B' + str(int(__import__('time').time()))[-6:],
    'batchName': '测试配租批次', 'orgId': ORG, 'securityType': 'PUBLIC',
    'houseCount': len(HOUSES), 'remark': '自动生成'})
batch_id = (r.get('data') or {}).get('id')
print('  %s 建批次 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                              batch_id, str(r.get('message'))[:60]))

if batch_id and HOUSES:
    r = call('POST', '/api/v1/allocation/batches/%s/houses' % batch_id,
             {'houseIds': HOUSES[:3]})
    print('  %s 房源入池 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                                    r.get('code'), str(r.get('message'))[:50]))
    r = call('POST', '/api/v1/allocation/batches/%s/status' % batch_id,
             {'batchStatus': 'PUBLISHED'})
    print('  %s 批次发布 → %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                                 r.get('code')))
    r = call('POST', '/api/v1/allocation/lottery',
             {'batchId': batch_id, 'seed': '20261020'})
    print('  %s 摇号 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                                r.get('code'), str(r.get('data') or r.get('message'))[:90]))
    res = call('GET', '/api/v1/allocation/lottery/%s' % batch_id)
    rr = res.get('data') or []
    print('  摇号结果 %d 条' % (len(rr) if isinstance(rr, list) else 0))

# ---------- 4) 配租单 ----------
al = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10')
print('\n  配租单 %s 条' % (al.get('data') or {}).get('total'))
for x in ((al.get('data') or {}).get('rows') or [])[:3]:
    print('    %s 人员%s 房源%s 状态%s' % (x.get('allocationNo'), x.get('personId'),
                                        x.get('houseId'), x.get('allocationStatus')))

D['batchId'] = batch_id
json.dump(D, open(r'D:\Work\业务平台开发\_验证\_test_data.json', 'w',
                  encoding='utf-8'), ensure_ascii=False, indent=1)
