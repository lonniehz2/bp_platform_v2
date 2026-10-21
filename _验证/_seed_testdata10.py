# -*- coding: utf-8 -*-
"""①修正 scan 为 GET ②生成 2026-11 未缴账单 ③催缴登记验证"""
import io
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']
FEE = D.get('feeItems', [])


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


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

# ---------- 1) 前端 scan 改 GET ----------
P = r'D:\Work\业务平台开发\frontend\src\api\modules.js'
s = io.open(P, encoding='utf-8').read()
if "req.post('/fin/dunnings/scan')" in s:
    s = s.replace("dunningScan: () => req.post('/fin/dunnings/scan'),",
                  "// 后端 scan 是 GET（不是 POST）\n"
                  "  dunningScan: (params) => req.get('/fin/dunnings/scan', { params }),")
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ modules.js：dunningScan 改为 GET')

# ---------- 2) 生成 2026-11 未缴账单 ----------
print('\n— 生成 2026-11 账单（不收款）—')
for fid in FEE:
    r = call('POST', '/api/v1/fin/bills/generate', {
        'orgId': ORG, 'feeItemId': fid,
        'periodStart': '2026-11-01', 'periodEnd': '2026-11-30', 'dryRun': False})
    d = r.get('data') or {}
    print('  %s 生成 %s 张，金额 %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                                      d.get('generated'), d.get('totalAmount')))

unpaid = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=5&billStatus=UNPAID')
rows = (unpaid.get('data') or {}).get('rows') or []
print('  未缴账单：%s 张' % (unpaid.get('data') or {}).get('total'))

# ---------- 3) 催缴：scan(GET) + 登记 ----------
print('\n— 催缴 —')
r = call('GET', '/api/v1/fin/dunnings/scan?orgId=%s' % ORG)
print('  %s scan(GET) → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                                 r.get('code'), str(r.get('data') or r.get('message'))[:80]))

if rows:
    b0 = rows[0]
    r = call('POST', '/api/v1/fin/dunnings', {
        'billId': b0['id'], 'personId': b0.get('personId'),
        'dunningType': 'SMS', 'dunningContent': '请尽快缴纳 2026-11 租金',
        'operatorId': 1})
    print('  %s 登记催缴 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                                    r.get('code'), str(r.get('message'))[:60]))

dn = call('GET', '/api/v1/fin/dunnings?pageNum=1&pageSize=5')
dr = (dn.get('data') or {}).get('rows') or []
print('  催缴记录 %s 条' % (dn.get('data') or {}).get('total'))
for x in dr[:3]:
    print('    账单%s 方式%s 内容%s' % (x.get('billId'), x.get('dunningType'),
                                     str(x.get('dunningContent'))[:24]))

# ---------- 4) 逾期扫描（账单逾期后）----------
r = call('POST', '/api/v1/fin/bills/scan-overdue')
print('\n  逾期扫描：%s %s' % (r.get('code'), str(r.get('data') or r.get('message'))[:60]))
