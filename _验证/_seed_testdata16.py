# -*- coding: utf-8 -*-
"""查看配租单创建接口参数，并生成配租单"""
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


# 1) 找配租单创建的入参
p = os.path.join(JAVA, 'biz', 'controller', 'AllocationController.java')
s = io.open(p, encoding='utf-8').read()
m = re.search(r'@PostMapping\s*\n\s*public R<AllocationVO>\s+(\w+)\(([^)]*)\)', s)
print('=== 配租单创建签名 ===')
if m:
    print('  方法 %s(%s)' % (m.group(1), re.sub(r'\s+', ' ', m.group(2))[:160]))
for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
    print('  record %s(%s)' % (mm.group(1), re.sub(r'\s+', ' ', mm.group(2))[:120]))

TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

# 2) 摇号结果
res = call('GET', '/api/v1/allocation/lottery/%s' % BATCH)
rows = res.get('data') or []
print('\n摇号结果 %d 条' % len(rows))
won = [x for x in rows if x.get('resultType') == 'WON']
print('WON %d 人' % len(won))

# 3) 批次的房源池
houses = call('GET', '/api/v1/allocation/batches/%s/houses' % BATCH)
hlist = houses.get('data') or []
if isinstance(hlist, dict):
    hlist = hlist.get('rows') or []
print('批次房源 %d 套' % len(hlist))
house_ids = [h if isinstance(h, str) else (h.get('houseId') or h.get('id'))
             for h in hlist][:len(won)]

# 4) 生成配租单（逐个）
print('\n— 生成配租单 —')
for i, w in enumerate(won):
    hid = house_ids[i] if i < len(house_ids) else None
    body = {'batchId': BATCH, 'personId': w.get('personId'),
            'houseId': hid, 'applicationId': w.get('applicationId'),
            'allocationType': 'LOTTERY'}
    r = call('POST', '/api/v1/allocation/allocations', body)
    print('  %s 人员%s 房源%s → %s %s'
          % ('✓' if r.get('code') == 'BP00000' else '✗', w.get('personId'), hid,
             r.get('code'), str(r.get('data') or r.get('message'))[:90]))

al = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10')
print('\n配租单 %d 条' % int((al.get('data') or {}).get('total') or 0))
for x in ((al.get('data') or {}).get('rows') or [])[:5]:
    print('  %s 人员%s 房源%s %s 锁定%s h'
          % (x.get('allocationNo'), x.get('personId'), x.get('houseId'),
             x.get('allocationStatus'), x.get('lockRemainHours')))
