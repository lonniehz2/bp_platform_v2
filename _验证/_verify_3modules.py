# -*- coding: utf-8 -*-
"""验证三个模块的写操作真实可用"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']
CONTRACT = (D.get('contracts') or [{}])[0].get('id')
ROOM = [r for r in D.get('rooms', []) if r][0]


def call(m, p, b=None, tok=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if tok:
        h['Authorization'] = 'Bearer ' + tok
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return -1, {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

print('=' * 72)
print(' ① 合同同住人')
st, r = call('POST', '/api/v1/contracts/%s/cohabitants' % CONTRACT, {
    'memberName': '测试配偶', 'relation': 'SPOUSE', 'idCardMask': '3506**********1234',
    'isGranted': 1}, TOK)
cid = (r.get('data') or {}).get('id')
print('   新增：%s %s → id=%s' % (st, r.get('code'), cid))

st, r = call('GET', '/api/v1/contracts/%s/cohabitants' % CONTRACT, None, TOK)
rows = r.get('data') or []
print('   列表：%s，%d 条' % (r.get('code'), len(rows) if isinstance(rows, list) else 0))

st, r = call('GET', '/api/v1/contracts/%s/cohabitants/household-size' % CONTRACT, None, TOK)
print('   家庭人口：%s %s' % (r.get('code'), r.get('data')))

if cid:
    st, r = call('POST', '/api/v1/contracts/%s/cohabitants/%s/grant' % (CONTRACT, cid),
                 {'granted': False}, TOK)
    print('   取消授权：%s %s' % (st, r.get('code')))
    st, r = call('DELETE', '/api/v1/contracts/%s/cohabitants/%s' % (CONTRACT, cid),
                 None, TOK)
    print('   删除：%s %s' % (st, r.get('code')))

print('\n' + '=' * 72)
print(' ② 计费项目')
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'TEST_PARK_' + str(int(__import__('time').time()))[-4:],
    'itemName': '测试停车费', 'itemType': 'PARKING', 'calcMode': 'BY_HOUSE',
    'unitPrice': 150.00, 'unit': '元/套·月'}, TOK)
fid = (r.get('data') or {}).get('id')
print('   新增：%s %s → id=%s' % (st, r.get('code'), fid))

if fid:
    st, r = call('POST', '/api/v1/fin/fee-items/%s/status' % fid,
                 {'status': 'DISABLED'}, TOK)
    print('   停用：%s %s' % (st, r.get('code')))
    st, r = call('POST', '/api/v1/fin/billing-rules', {
        'feeItemId': fid, 'ruleName': '停车费标准规则',
        'effectiveDate': '2026-11-01', 'unitPrice': 150.00, 'orgId': ORG}, TOK)
    rid = (r.get('data') or {}).get('id')
    print('   计费规则：%s %s → id=%s' % (st, r.get('code'), rid))
    if rid:
        st, r = call('POST', '/api/v1/fin/billing-rules/%s/approve' % rid, None, TOK)
        print('   规则审批：%s %s' % (st, r.get('code')))
    st, r = call('POST', '/api/v1/fin/calc-preview', {
        'feeItemId': fid, 'area': 60, 'quantity': 1}, TOK)
    print('   试算：%s %s' % (st, r.get('data') or r.get('message') or r.get('code')))

print('\n' + '=' * 72)
print(' ③ 空间新增/删除')
st, r = call('POST', '/api/v1/spaces', {
    'orgId': ORG, 'parentId': ROOM, 'spaceCode': 'TESTBED1',
    'spaceName': '测试床位', 'spaceType': 'BED', 'area': 12, 'sortNo': 1}, TOK)
sid = (r.get('data') or {}).get('id')
print('   新增 BED：%s %s → id=%s %s' % (st, r.get('code'), sid,
                                        str(r.get('message'))[:40]))
if sid:
    st, r = call('DELETE', '/api/v1/spaces/%s' % sid, None, TOK)
    print('   删除：%s %s' % (st, r.get('code')))
st, r = call('DELETE', '/api/v1/spaces/%s' % ROOM, None, TOK)
print('   删除有下级的房间（应被拒）：%s %s' % (st, r.get('code'),
                                            str(r.get('message'))[:50]))
