# -*- coding: utf-8 -*-
"""补充可测试的业务数据：组织→空间→房源→人员→合同→账单→押金→公示

全部通过真实接口创建（走状态机与业务校验），保证数据合法可用。
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
CREATED = {}


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__, 'message': str(e)}


def ok(r, tag):
    c = r.get('code')
    if c == 'BP00000':
        print('  ✓ %s' % tag)
        return True
    print('  ✗ %s → %s %s' % (tag, c, str(r.get('message'))[:70]))
    return False


sfx = str(int(time.time()))[-5:]
print('=' * 70)
print(' 补充测试数据（真实接口）')
print('=' * 70)

TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')
print('登录：%s' % ('OK' if TOK else 'FAIL'))
if not TOK:
    sys.exit(1)

# ---------- 1) 组织（小区）----------
r = call('POST', '/api/v1/orgs', {
    'orgName': '测试小区' + sfx, 'orgCode': 'TEST' + sfx, 'orgType': 'PROJECT',
    'parentId': None, 'status': 'ENABLED', 'regionCode': '350600'})
org_id = (r.get('data') or {}).get('id')
ok(r, '小区 %s → id=%s' % ('测试小区' + sfx, org_id))

# ---------- 2) 空间层级 BUILDING→UNIT→FLOOR→ROOM ----------
def create_space(name, stype, parent, path):
    rr = call('POST', '/api/v1/spaces', {
        'spaceName': name, 'spaceType': stype, 'parentId': parent,
        'orgId': org_id, 'pathCode': path, 'status': 'ENABLED'})
    return (rr.get('data') or {}).get('id'), rr


b_id, rb = create_space('1号楼', 'BUILDING', org_id, '01')
ok(rb, '楼栋 id=%s' % b_id)
u_id, ru = create_space('1单元', 'UNIT', b_id, '0101')
ok(ru, '单元 id=%s' % u_id)
f_id, rf = create_space('1层', 'FLOOR', u_id, '010101')
ok(rf, '楼层 id=%s' % f_id)

rooms = []
for i in range(1, 6):
    rid, rr = create_space('%d0%d' % (1, i), 'ROOM', f_id, '010101%02d' % i)
    if (rr.get('code') == 'BP00000'):
        rooms.append(rid)
    print('  房间 %d → id=%s (%s)' % (i, rid, rr.get('code')))

# ---------- 3) 房源 ----------
houses = []
for i, sp in enumerate(rooms, 1):
    rr = call('POST', '/api/v1/houses', {
        'orgId': org_id, 'spaceId': sp, 'houseCode': 'T%s-%02d' % (sfx, i),
        'houseName': '测试房源%d' % i, 'houseType': 'PUBLIC_RENTAL',
        'securityType': 'PUBLIC', 'area': 60 + i * 5, 'rentStandard': 12.5,
        'rentUnit': 'MONTH', 'maxCapacity': 4, 'houseStatus': 'VACANT'})
    hid = (rr.get('data') or {}).get('id')
    if rr.get('code') == 'BP00000':
        houses.append(hid)
    print('  房源 %d → id=%s (%s)' % (i, hid, rr.get('code')))

# ---------- 4) 人员 ----------
persons = []
for i in range(1, 6):
    rr = call('POST', '/api/v1/persons', {
        'personName': '测试租户%d' % i,
        'idCard': '3506001990010%05d' % (i * 111 + int(sfx) % 1000),
        'phone': '1380013%04d' % (i * 111 % 10000), 'personType': 'TENANT',
        'gender': 'MALE' if i % 2 else 'FEMALE'})
    pid = (rr.get('data') or {}).get('id')
    if rr.get('code') == 'BP00000':
        persons.append({'id': pid, 'name': '测试租户%d' % i})
    print('  人员 %d → id=%s (%s) %s' % (i, pid, rr.get('code'),
                                       str(rr.get('message'))[:40]))

# ---------- 5) 合同 ----------
contracts = []
for i, (h, p) in enumerate(zip(houses, persons)):
    rr = call('POST', '/api/v1/contracts', {
        'contractType': 'PUBLIC_RENTAL', 'orgId': org_id, 'lessorOrgId': org_id,
        'lesseePersonId': p['id'], 'lesseeName': p['name'],
        'lesseePhone': '1380013%04d' % (i * 111 % 10000),
        'houseId': h, 'spaceId': rooms[i] if i < len(rooms) else None,
        'houseAddress': '测试小区1号楼1单元10%d' % (i + 1),
        'houseArea': 60 + (i + 1) * 5,
        'leaseStart': '2026-01-01', 'leaseEnd': '2026-12-31',
        'rentPrice': 12.5, 'rentUnit': 'MONTH', 'monthlyRent': 1000 + i * 100,
        'depositAmount': 1000, 'subsidyAmount': 200, 'payCycle': 'MONTH',
        'payDay': 5, 'signType': 'OFFLINE'})
    cid = (rr.get('data') or {}).get('id')
    if rr.get('code') == 'BP00000':
        contracts.append({'id': cid, 'personId': p['id'], 'houseId': h})
    print('  合同 %d → id=%s (%s) %s' % (i + 1, cid, rr.get('code'),
                                       str(rr.get('message'))[:40]))

# ---------- 6) 签约 ----------
signed = 0
for c in contracts:
    rr = call('POST', '/api/v1/contracts/%s/sign' % c['id'],
              {'signVendor': 'OFFLINE', 'reason': '测试数据'})
    if rr.get('code') == 'BP00000':
        signed += 1
    else:
        print('  签约失败 id=%s → %s %s' % (c['id'], rr.get('code'),
                                          str(rr.get('message'))[:50]))
print('  已签约 %d / %d' % (signed, len(contracts)))

# ---------- 7) 押金台账 ----------
dep_ok = 0
for c in contracts:
    rr = call('POST', '/api/v1/fin/deposits', {
        'contractId': c['id'], 'personId': c['personId'],
        'depositAmount': 1000, 'paidAmount': 1000, 'capAmount': 1000,
        'isExempt': 0})
    if rr.get('code') == 'BP00000':
        dep_ok += 1
print('  押金台账 %d / %d' % (dep_ok, len(contracts)))

CREATED = {'orgId': org_id, 'buildingId': b_id, 'rooms': rooms,
           'houses': houses, 'persons': persons, 'contracts': contracts}
io_path = r'D:\Work\业务平台开发\_验证\_test_data.json'
open(io_path, 'w', encoding='utf-8').write(
    json.dumps(CREATED, ensure_ascii=False, indent=1))
print('\n已保存：%s' % io_path)
print('汇总：组织1 / 空间%d / 房源%d / 人员%d / 合同%d / 押金%d'
      % (len(rooms), len(houses), len(persons), len(contracts), dep_ok))
