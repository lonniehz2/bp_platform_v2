# -*- coding: utf-8 -*-
"""建收费项目 → 合同（补 spaceId + signType=PAPER）→ 签约 → 押金 → 出账"""
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


def show(r, tag):
    c = r.get('code')
    d = (r.get('data') or {}).get('id')
    print('  %s %-24s %s %s' % ('✓' if c == 'BP00000' else '✗', tag, c,
                                ('id=%s' % d) if d else str(r.get('message'))[:60]))
    return d


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

print('— 收费项目 —')
FEE = [
    ('RENT' + str(int(time.time()))[-4:], '租金', 'RENT', 'BY_AREA', 12.5, '元/㎡·月'),
    ('PROP' + str(int(time.time()))[-4:], '物业费', 'PROPERTY', 'BY_AREA', 2.5, '元/㎡·月'),
]
fee_ids = []
for code, name, typ, mode, price, unit in FEE:
    fid = show(call('POST', '/api/v1/fin/fee-items', {
        'itemCode': code, 'itemName': name, 'itemType': typ, 'calcMode': mode,
        'unitPrice': price, 'unit': unit, 'securityType': 'PUBLIC'}), name)
    if fid:
        fee_ids.append(fid)

print('\n— 合同（signType=PAPER）—')
contracts = []
for i, (hid, rid, pid) in enumerate(zip(HOUSES, ROOMS, PERSONS), 1):
    cid = show(call('POST', '/api/v1/contracts', {
        'contractType': 'PUBLIC_RENTAL', 'orgId': ORG, 'lessorOrgId': ORG,
        'lesseePersonId': pid, 'lesseeName': '测试租户%d' % i,
        'lesseePhone': '138%08d' % (10000000 + i * 1111),
        'houseId': hid, 'spaceId': rid,
        'houseAddress': '测试小区1号楼1单元10%d室' % i,
        'houseArea': 60 + i * 5, 'leaseStart': '2026-01-01',
        'leaseEnd': '2026-12-31', 'rentPrice': 12.5, 'rentUnit': 'AREA_MONTH',
        'monthlyRent': 1000 + i * 100, 'depositAmount': 1000,
        'subsidyAmount': 200, 'payCycle': 'MONTH', 'payDay': 5,
        'signType': 'PAPER'}), '合同%d' % i)
    if cid:
        contracts.append({'id': cid, 'personId': pid, 'houseId': hid})

print('\n— 签约 —')
for c in contracts:
    r = call('POST', '/api/v1/contracts/%s/sign' % c['id'],
             {'signVendor': 'PAPER', 'reason': '测试数据'})
    print('  %s %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗', c['id'],
                         str(r.get('message'))[:44]))

print('\n— 押金 —')
for c in contracts:
    r = call('POST', '/api/v1/fin/deposits', {
        'contractId': c['id'], 'personId': c['personId'],
        'depositAmount': 1000, 'paidAmount': 1000, 'capAmount': 1000,
        'isExempt': 0})
    print('  %s %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗', c['id'],
                         str(r.get('message'))[:44]))

print('\n— 出账（按收费项目+账期）—')
for fid in fee_ids:
    r = call('POST', '/api/v1/fin/bills/generate', {
        'orgId': ORG, 'feeItemId': fid,
        'periodStart': '2026-10-01', 'periodEnd': '2026-10-31',
        'dryRun': False})
    print('  %s feeItem=%s → %s %s' % ('✓' if r.get('code') == 'BP00000' else '✗',
                                      fid, r.get('code'),
                                      str(r.get('data') or r.get('message'))[:100]))

D.update({'contracts': contracts, 'feeItems': fee_ids})
json.dump(D, open(r'D:\Work\业务平台开发\_验证\_test_data.json', 'w',
                  encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n汇总：收费项目%d 合同%d' % (len(fee_ids), len(contracts)))
