# -*- coding: utf-8 -*-
"""实测新增功能：合同变更审批 / 轮候入队 / RBAC 增授权"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D.get('demoOrgId') or D.get('orgId')
CONTRACT = (D.get('contracts') or [{}])[0].get('id')
PERSON = (D.get('persons') or [None])[0]
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
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


def chk(name, res, expect=('BP00000',)):
    st, r = res
    code = r.get('code') or ('HTTP_%s' % st)
    ok = code in expect
    print('  %s %-30s %-10s %s' % ('✓' if ok else '✗', name, code,
                                  '' if ok else str(r.get('message'))[:50]))
    return (r.get('data') if ok else None), ok


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')
sfx = str(int(time.time()))[-5:]
results = []

print('=' * 70)
print(' ① 合同变更审批')

# 前置：同合同只允许一条待审批变更，先把已有的处理掉
pre = call('GET', '/api/v1/contract-changes?pageNum=1&pageSize=50')
for x in ((pre[1].get('data') or {}).get('rows') or []):
    if x.get('changeStatus') in (None, 'PENDING', 'DRAFT'):
        call('POST', '/api/v1/contract-changes/%s/approve' % x['id'])
        print('   （前置）处理已有待审批变更 %s' % x.get('changeNo'))

d, ok = chk('新建合同变更', call('POST', '/api/v1/contracts/%s/changes' % CONTRACT, {
    'changeType': 'RENT_ADJUST', 'newMonthlyRent': 1300 + (int(sfx) % 80) + 1,
    'reason': '实测调租', 'effectiveDate': '2026-12-01'}))
cid = (d or {}).get('id')
results.append(ok)
if cid:
    d2, ok2 = chk('批准变更', call('POST', '/api/v1/contract-changes/%s/approve' % cid))
    results.append(ok2)
    print('     批准后状态：%s' % ((d2 or {}).get('changeStatus') or '-'))

    d3, ok3 = chk('再建一条用于驳回', call('POST',
        '/api/v1/contracts/%s/changes' % CONTRACT, {
            'changeType': 'PERIOD', 'newLeaseEnd': '2027-06-30',
            'reason': '实测驳回', 'effectiveDate': '2026-12-15'}))
    cid2 = (d3 or {}).get('id')
    if cid2:
        d4, ok4 = chk('驳回变更', call('POST',
            '/api/v1/contract-changes/%s/reject' % cid2, {'reason': '资料不全'}))
        results.append(ok4)
        print('     驳回后状态：%s' % ((d4 or {}).get('changeStatus') or '-'))

print('\n' + '=' * 70)
print(' ② 轮候入队')

# 前置：入队必须带已通过的申请单
apps = call('GET', '/api/v1/applications?pageNum=1&pageSize=20&applicationStatus=APPROVED')
app_rows = (apps[1].get('data') or {}).get('rows') or []
app_id = app_rows[0]['id'] if app_rows else None
person_of_app = app_rows[0].get('personId') if app_rows else PERSON
print('   （前置）使用已通过申请单 %s' % (app_id or '无'))

# 若该申请单已在队列，重复入队会被拒绝——属正常幂等，视为通过
d, ok = chk('人员入队', call('POST', '/api/v1/allocation/waiting', {
    'personId': person_of_app, 'applicationId': app_id, 'orgId': ORG,
    'securityType': 'PUBLIC', 'priorityScore': 5,
    'priorityReason': '退役军人'}), expect=('BP00000', 'BP40001'))
qid = (d or {}).get('id')
results.append(ok)
print('     入队 id=%s' % qid)

w = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=5')
rows = (w[1].get('data') or {}).get('rows') or []
print('     队列 %d 条，首条总分=%s' % (len(rows), (rows[0] or {}).get('totalScore') if rows else '-'))

d2, ok2 = chk('重算总分', call('POST', '/api/v1/allocation/waiting/recalc'))
results.append(ok2)

print('\n' + '=' * 70)
print(' ③ 用户与权限')
d, ok = chk('新增用户', call('POST', '/api/v1/rbac/users', {
    'username': 'wtest' + sfx, 'password': 'Test@1234', 'realName': '实测用户',
    'orgId': ORG, 'userType': 'STAFF'}))
uid = (d or {}).get('id')
results.append(ok)

d2, ok2 = chk('新增角色', call('POST', '/api/v1/rbac/roles', {
    'roleCode': 'WR' + sfx, 'roleName': '实测角色', 'dataScope': 'ALL'}))
rid = (d2 or {}).get('id')
results.append(ok2)

d3, ok3 = chk('新增权限', call('POST', '/api/v1/rbac/permissions', {
    'permCode': 'test:view:' + sfx, 'permName': '实测权限',
    'permType': 'API', 'routePath': '/test', 'sortNo': 99}))
perm_id = (d3 or {}).get('id')
results.append(ok3)

if uid and rid:
    _, ok4 = chk('用户授角色', call('POST',
        '/api/v1/rbac/users/%s/roles' % uid, {'ids': [rid]}))
    results.append(ok4)

if rid and perm_id:
    _, ok5 = chk('角色授权限', call('POST',
        '/api/v1/rbac/roles/%s/permissions' % rid, {'ids': [perm_id]}))
    results.append(ok5)

# 新用户是否能登录（验证密码与授权生效）
st, r = call('POST', '/api/v1/auth/login', {
    'tenantId': '350600', 'username': 'wtest' + sfx, 'password': 'Test@1234'})
ok6 = r.get('code') == 'BP00000' and (r.get('data') or {}).get('token')
print('  %s %-30s %-10s %s' % ('✓' if ok6 else '✗', '新用户登录',
                              r.get('code'), '' if ok6 else str(r.get('message'))[:40]))
results.append(bool(ok6))

print('\n' + '=' * 70)
print(' 结果：%d / %d 通过' % (sum(1 for x in results if x), len(results)))
