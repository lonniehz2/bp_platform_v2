# -*- coding: utf-8 -*-
"""续建：空间（顶层无父）→ 房源 → 合同 → 签约 → 押金 → 出账"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']
PERSONS = D['persons']


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__, 'message': str(e)}


def show(r, tag):
    c = r.get('code')
    d = (r.get('data') or {}).get('id')
    print('  %s %-30s %s %s' % ('✓' if c == 'BP00000' else '✗', tag, c,
                                ('id=%s' % d) if d else str(r.get('message'))[:56]))
    return d


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')
sfx = str(int(time.time()))[-5:]

print('— 空间（顶层 parentId=null）—')
def sp(code, name, stype, parent=None, area=None):
    body = {'orgId': ORG, 'spaceCode': code, 'spaceName': name,
            'spaceType': stype, 'sortNo': 1}
    if parent:
        body['parentId'] = parent
    if area:
        body['area'] = area
    return show(call('POST', '/api/v1/spaces', body), '%s %s' % (stype, name))

b = sp('B' + sfx, '1号楼', 'BUILDING')
u = sp('B' + sfx + 'U1', '1单元', 'UNIT', b)
f = sp('B' + sfx + 'U1F1', '1层', 'FLOOR', u)
rooms = [sp('B%sU1F1R%d' % (sfx, i), '10%d室' % i, 'ROOM', f) for i in range(1, 6)]

print('\n— 房源 —')
houses = []
for i, rid in enumerate([r for r in rooms if r], 1):
    hid = show(call('POST', '/api/v1/houses', {
        'spaceId': rid, 'houseCode': 'H%s%02d' % (sfx, i),
        'houseName': '测试房源%d' % i, 'houseType': 'PUBLIC_RENTAL',
        'structType': 'MULTI', 'useType': 'CIVIL', 'unitLayout': '2室1厅',
        'floorNo': 1, 'orientation': 'SOUTH', 'area': 60 + i * 5,
        'rentStandard': 12.5, 'rentUnit': 'MONTH', 'maxCapacity': 4}), '房源%d' % i)
    if hid:
        houses.append(hid)

print('\n— 合同 —')
contracts = []
for i, (hid, pid) in enumerate(zip(houses, PERSONS), 1):
    cid = show(call('POST', '/api/v1/contracts', {
        'contractType': 'PUBLIC_RENTAL', 'orgId': ORG, 'lessorOrgId': ORG,
        'lesseePersonId': pid, 'lesseeName': '测试租户%d' % i,
        'lesseePhone': '138%08d' % (10000000 + i * 1111),
        'houseId': hid, 'houseAddress': '测试小区1号楼1单元10%d室' % i,
        'houseArea': 60 + i * 5, 'leaseStart': '2026-01-01',
        'leaseEnd': '2026-12-31', 'rentPrice': 12.5, 'rentUnit': 'MONTH',
        'monthlyRent': 1000 + i * 100, 'depositAmount': 1000,
        'subsidyAmount': 200, 'payCycle': 'MONTH', 'payDay': 5,
        'signType': 'OFFLINE'}), '合同%d' % i)
    if cid:
        contracts.append({'id': cid, 'personId': pid, 'houseId': hid})

print('\n— 签约 —')
signed = 0
for c in contracts:
    r = call('POST', '/api/v1/contracts/%s/sign' % c['id'],
             {'signVendor': 'OFFLINE', 'reason': '测试数据'})
    if r.get('code') == 'BP00000':
        signed += 1
    else:
        print('   签约失败 %s → %s %s' % (c['id'], r.get('code'),
                                        str(r.get('message'))[:50]))
print('  已签约 %d / %d' % (signed, len(contracts)))

print('\n— 押金台账 —')
deps = 0
for c in contracts:
    r = call('POST', '/api/v1/fin/deposits', {
        'contractId': c['id'], 'personId': c['personId'],
        'depositAmount': 1000, 'paidAmount': 1000, 'capAmount': 1000,
        'isExempt': 0})
    if r.get('code') == 'BP00000':
        deps += 1
print('  押金台账 %d / %d' % (deps, len(contracts)))

D.update({'building': b, 'unit': u, 'floor': f, 'rooms': rooms,
          'houses': houses, 'contracts': contracts})
json.dump(D, open(r'D:\Work\业务平台开发\_验证\_test_data.json', 'w',
                  encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n汇总：空间%d 房源%d 合同%d 签约%d 押金%d'
      % (len([r for r in rooms if r]), len(houses), len(contracts), signed, deps))
