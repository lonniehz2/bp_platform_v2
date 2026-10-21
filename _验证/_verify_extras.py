# -*- coding: utf-8 -*-
"""验证扩展操作台 6 类写操作"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']
HOUSE = (D.get('houses') or [None])[0]


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
print(' ① 消息待办')
st, r = call('POST', '/api/v1/messages/todos', {
    'userId': 1, 'todoType': 'APPROVAL', 'title': '测试待办',
    'content': '请在时限内处理', 'bizType': 'APPLICATION', 'bizId': 1,
    'dueTime': '2026-12-31 18:00:00'}, TOK)
tid = (r.get('data') or {}).get('id')
print('   新增待办：%s %s id=%s' % (st, r.get('code'), tid))
if tid:
    st, r = call('POST', '/api/v1/messages/todos/%s/read' % tid, None, TOK)
    print('   标记已读：%s %s' % (st, r.get('code')))
    st, r = call('POST', '/api/v1/messages/todos/%s/done' % tid, None, TOK)
    print('   办结：%s %s' % (st, r.get('code')))
st, r = call('POST', '/api/v1/messages/retry-failed?limit=5', None, TOK)
print('   重推失败：%s %s' % (st, r.get('code')))

print('\n' + '=' * 72)
print(' ② 告警规则')
st, r = call('POST', '/api/v1/rules/rulesets', {
    'code': 'RS_VERIFY_' + str(int(__import__('time').time()))[-4:],
    'name': '测试规则集', 'domain': 'FINANCE', 'scenario': 'ARREAR',
    'securityType': 'PUBLIC', 'version': 'v1', 'description': '验证'}, TOK)
rsid = (r.get('data') or {}).get('id')
print('   新增规则集：%s %s id=%s %s' % (st, r.get('code'), rsid,
                                      str(r.get('message'))[:40]))
if rsid:
    st, r = call('POST', '/api/v1/rules/rulesets/%s/rules' % rsid, {
        'code': 'R1', 'name': '欠费比例告警', 'conditionExpr': 'arrearRate > 15',
        'thresholdJson': '{"threshold":15}', 'severity': 'WARNING',
        'eventType': 'ARREAR_RATE'}, TOK)
    print('   加规则：%s %s' % (st, r.get('code')))
    st, r = call('POST', '/api/v1/rules/rulesets/%s/publish' % rsid, None, TOK)
    print('   发布：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:36]))
    st, r = call('POST', '/api/v1/rules/rulesets/%s/execute' % rsid,
                 {'bizType': 'ARREAR', 'bizId': 1, 'actual': 20.5, 'count': 1,
                  'eventType': 'TEST'}, TOK)
    print('   执行测试：%s %s %s' % (st, r.get('code'),
                                  str(r.get('data') or r.get('message'))[:60]))

print('\n' + '=' * 72)
print(' ③ 开放平台')
st, r = call('GET', '/api/v1/open/apps', None, TOK)
apps = r.get('data') or []
aid = (apps[0].get('id') if isinstance(apps, list) and apps else None)
print('   应用数：%d' % (len(apps) if isinstance(apps, list) else 0))
if aid:
    st, r = call('POST', '/api/v1/open/apps/%s/status' % aid,
                 {'status': 'DISABLED'}, TOK)
    print('   停用应用：%s %s' % (st, r.get('code')))
    st, r = call('POST', '/api/v1/open/apps/%s/reset-secret' % aid, None, TOK)
    print('   重置密钥：%s %s' % (st, r.get('code')))
st, r = call('POST', '/api/v1/open/webhooks', {
    'hookName': '测试回调', 'callbackUrl': 'https://example.com/cb',
    'eventTypes': 'contract.effective', 'retryTimes': 3,
    'hookStatus': 'ENABLED'}, TOK)
print('   新增 Webhook：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:40]))

print('\n' + '=' * 72)
print(' ④ 权限管理')
st, r = call('POST', '/api/v1/rbac/roles', {
    'roleCode': 'AUDITOR', 'roleName': '稽核员', 'dataScope': 'ALL'}, TOK)
roleid = (r.get('data') or {}).get('id')
print('   新增角色：%s %s id=%s %s' % (st, r.get('code'), roleid,
                                    str(r.get('message'))[:40]))
if roleid:
    st, r = call('POST', '/api/v1/rbac/roles/%s/permissions' % roleid,
                 {'ids': [790000000000000001]}, TOK)
    print('   角色授权限：%s %s' % (st, r.get('code')))
st, r = call('POST', '/api/v1/rbac/users', {
    'username': 'auditor01', 'password': 'Audit@123', 'realName': '稽核员甲',
    'orgId': ORG, 'userType': 'STAFF'}, TOK)
uid = (r.get('data') or {}).get('id')
print('   新增用户：%s %s id=%s %s' % (st, r.get('code'), uid,
                                    str(r.get('message'))[:40]))
if uid and roleid:
    st, r = call('POST', '/api/v1/rbac/users/%s/roles' % uid,
                 {'ids': [roleid]}, TOK)
    print('   用户授角色：%s %s' % (st, r.get('code')))

print('\n' + '=' * 72)
print(' ⑤ 通行授权撤销')
st, r = call('GET', '/api/v1/grants?pageNum=1&pageSize=5', None, TOK)
gs = (r.get('data') or {}).get('rows') or []
print('   授权数：%d' % len(gs))
if gs:
    st, r = call('POST', '/api/v1/grants/%s/revoke' % gs[0]['id'],
                 {'reason': '测试撤销'}, TOK)
    print('   撤销：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:36]))

print('\n' + '=' * 72)
print(' ⑥ 日房态')
st, r = call('POST', '/api/v1/house-calendar/%s/ensure?month=2026-12' % HOUSE,
             None, TOK)
print('   生成房态：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:40]))
st, r = call('POST', '/api/v1/house-calendar/%s/price' % HOUSE, {
    'calendarDate': '2026-12-01', 'price': 220.00}, TOK)
print('   改价：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:40]))
st, r = call('POST', '/api/v1/house-calendar/%s/status' % HOUSE, {
    'calendarDate': '2026-12-01', 'dayStatus': 'LOCKED'}, TOK)
print('   改状态：%s %s %s' % (st, r.get('code'), str(r.get('message'))[:40]))
