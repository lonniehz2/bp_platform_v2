# -*- coding: utf-8 -*-
"""修正 rentUnit 后建房源 → 合同 → 签约 → 押金 → 出账"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG, PERSONS = D['orgId'], D['persons']
ROOMS = [r for r in D.get('rooms', []) if r]


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
    print('  %s %-26s %s %s' % ('✓' if c == 'BP00000' else '✗', tag, c,
                                ('id=%s' % d) if d else str(r.get('message'))[:56]))
    return d


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')
sfx = str(int(time.time()))[-5:]

print('— 房源（rentUnit=AREA_MONTH）—')
houses = []
for i, rid in enumerate(ROOMS, 1):
    hid = show(call('POST', '/api/v1/houses', {
        'spaceId': rid, 'houseCode': 'H%s%02d' % (sfx, i),
        'houseName': '测试房源%d' % i, 'houseType': 'PUBLIC_RENTAL',
        'structType': 'MULTI', 'useType': 'CIVIL', 'unitLayout': '2室1厅',
        'floorNo': 1, 'orientation': 'SOUTH', 'area': 60 + i * 5,
        'rentStandard': 12.5, 'rentUnit': 'AREA_MONTH', 'maxCapacity': 4,
        'securityType': 'PUBLIC'}), '房源%d' % i)
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
        'leaseEnd': '2026-12-31', 'rentPrice': 12.5, 'rentUnit': 'AREA_MONTH',
        'monthlyRent': 1000 + i * 100, 'depositAmount': 1000,
        'subsidyAmount': 200, 'payCycle': 'MONTH', 'payDay': 5,
        'signType': 'OFFLINE'}), '合同%d' % i)
    if cid:
        contracts.append({'id': cid, 'personId': pid, 'houseId': hid})

print('\n— 签约 —')
for c in contracts:
    r = call('POST', '/api/v1/contracts/%s/sign' % c['id'],
             {'signVendor': 'OFFLINE', 'reason': '测试数据'})
    print('  %s 合同 %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                              c['id'], str(r.get('message'))[:46]))

print('\n— 押金 —')
for c in contracts:
    r = call('POST', '/api/v1/fin/deposits', {
        'contractId': c['id'], 'personId': c['personId'],
        'depositAmount': 1000, 'paidAmount': 1000, 'capAmount': 1000,
        'isExempt': 0})
    print('  %s 押金 %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                              c['id'], str(r.get('message'))[:46]))

print('\n— 批量出账 —')
r = call('POST', '/api/v1/fin/bills/generate', {
    'orgId': ORG, 'billPeriod': '2026-10', 'dryRun': False})
print('  %s 出账 → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                            r.get('code'), str(r.get('data') or r.get('message'))[:120]))

D.update({'houses': houses, 'contracts': contracts})
json.dump(D, open(r'D:\Work\业务平台开发\_验证\_test_data.json', 'w',
                  encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n汇总：房源%d 合同%d' % (len(houses), len(contracts)))
