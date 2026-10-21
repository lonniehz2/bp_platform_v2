# -*- coding: utf-8 -*-
"""修正 house_ids 解析并创建配租单"""
import io
import json
import urllib.error
import urllib.request

P = r'D:\Work\业务平台开发\_验证\_seed_testdata16.py'
s = io.open(P, encoding='utf-8').read()
old = "house_ids = [h.get('houseId') or h.get('id') for h in hlist][:len(won)]"
new = ("house_ids = [h if isinstance(h, str) else (h.get('houseId') or h.get('id'))\n"
       "             for h in hlist][:len(won)]")
if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已修正 house_ids 解析')
else:
    print('锚点未找到')

# 直接续跑创建逻辑
BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
BATCH = D.get('batchId')


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
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


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

rows = (call('GET', '/api/v1/allocation/lottery/%s' % BATCH, tok=TOK).get('data') or [])
won = [x for x in rows if x.get('resultType') == 'WON']
hlist = (call('GET', '/api/v1/allocation/batches/%s/houses' % BATCH, tok=TOK)
         .get('data') or [])
if isinstance(hlist, dict):
    hlist = hlist.get('rows') or []
hids = [h if isinstance(h, str) else (h.get('houseId') or h.get('id')) for h in hlist]
print('WON %d，房源 %d' % (len(won), len(hids)))

print('\n— 生成配租单 —')
for i, w in enumerate(won):
    hid = hids[i] if i < len(hids) else None
    for body in (
            {'batchId': BATCH, 'personId': w.get('personId'), 'houseId': hid,
             'applicationId': w.get('applicationId'), 'allocationType': 'LOTTERY'},
            {'batchId': BATCH, 'queueId': w.get('queueId'), 'houseId': hid,
             'allocationType': 'LOTTERY'}):
        r = call('POST', '/api/v1/allocation/allocations', body, TOK)
        print('  %s 人员%s 房源%s → %s %s'
              % ('✓' if r.get('code') == 'BP00000' else '✗', w.get('personId'), hid,
                 r.get('code'), str(r.get('message') or r.get('data'))[:80]))
        if r.get('code') == 'BP00000':
            break

al = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=10', tok=TOK)
print('\n配租单 %d 条' % int((al.get('data') or {}).get('total') or 0))
for x in ((al.get('data') or {}).get('rows') or [])[:5]:
    print('  %s 人员%s 房源%s %s'
          % (x.get('allocationNo'), x.get('personId'), x.get('houseId'),
             x.get('allocationStatus')))
