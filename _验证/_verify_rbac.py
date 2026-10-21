# -*- coding: utf-8 -*-
"""RBAC 验证：鉴权是否真正生效（401/403/放行）"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
JSON_H = {'Content-Type': 'application/json'}
TENANT = '350600'


def call(m, p, b=None, token=None, headers=None):
    h = dict(JSON_H)
    h['X-Tenant-Id'] = TENANT
    if token:
        h['Authorization'] = 'Bearer ' + token
    if headers:
        h.update(headers)
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            raw = x.read().decode('utf-8', 'replace')
            try:
                return x.status, json.loads(raw)
            except Exception:
                return x.status, {'code': 'HTML', 'size': len(raw)}
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}


ok = fail = 0


def chk(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1
        print('  [PASS] ' + name)
    else:
        fail += 1
        print('  [FAIL] ' + name + '  ' + str(extra))


sfx = str(int(time.time()))[-6:]
print('=' * 78)
print(' RBAC 验证 · 鉴权是否真正生效')
print('=' * 78)

# ---------- 1. 免鉴权接口 ----------
st, r = call('GET', '/actuator/health')
chk('健康检查免鉴权', st == 200, st)
st, r = call('GET', '/')
chk('首页免鉴权', st == 200, st)

# ---------- 2. 无令牌 → 401 ----------
st, r = call('GET', '/api/v1/orgs?pageNum=1&pageSize=5')
chk('⭐⭐ 无令牌访问业务接口 → 401', st == 401,
    'http=%s code=%s' % (st, r.get('code')))
chk('返回码 BP20001（未登录）', r.get('code') == 'BP20001', r.get('code'))
print('     拒绝信息：%s' % r.get('message'))

st, r = call('POST', '/api/v1/orgs', {'orgCode': 'X' + sfx, 'orgName': 'x',
                                      'orgType': 'COMMUNITY'})
chk('⭐⭐ 无令牌写操作 → 401', st == 401, st)

st, r = call('GET', '/api/v1/houses/1', token='bogus-token-xxx')
chk('⭐ 伪造令牌 → 401', st == 401, st)

# ---------- 3. 登录 ----------
st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123', 'deviceType': 'WEB'})
chk('⭐ 管理员登录成功', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
adminTok = (r.get('data') or {}).get('token')
chk('返回令牌', bool(adminTok), adminTok)
chk('标记为管理员', (r.get('data') or {}).get('admin') in (True, 'true'),
    (r.get('data') or {}).get('admin'))
print('     admin 令牌：%s...' % (adminTok or '')[:16])

st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'admin', 'password': 'WRONG'})
chk('⭐ 密码错误被拒', r.get('code') == 'BP10001', r.get('code'))
chk('不泄露账号是否存在', '登录名或密码错误' in str(r.get('message')), r.get('message'))

st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'nosuchuser', 'password': 'x'})
chk('不存在的账号同样话术', '登录名或密码错误' in str(r.get('message')), r.get('message'))

# ---------- 4. 带令牌访问 → 放行 ----------
st, r = call('GET', '/api/v1/orgs?pageNum=1&pageSize=5', token=adminTok)
chk('⭐⭐ 管理员带令牌可访问业务接口', st == 200 and r.get('code') == 'BP00000',
    'http=%s code=%s' % (st, r.get('code')))

# 多租户上下文由令牌注入（不用再传 X-Tenant-Id）
st, r = call('GET', '/api/v1/orgs?pageNum=1&pageSize=5', token=adminTok,
             headers={'X-Tenant-Id': ''})
chk('⭐⭐ 租户上下文由令牌自动注入', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 5. /me 返回权限 ----------
st, r = call('GET', '/api/v1/auth/me', token=adminTok)
me = r.get('data') or {}
chk('⭐ /me 返回用户信息', me.get('username') == 'admin', me.get('username'))
chk('管理员返回通配权限 *',
    '*' in (me.get('permissions') or []) or me.get('admin') in (True, 'true'),
    me.get('permissions'))

# ---------- 6. ⭐⭐ 权限校验（403）----------
st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'acceptor', 'password': 'acc123'})
accTok = (r.get('data') or {}).get('token')
chk('受理员登录成功', bool(accTok), r.get('code'))

st, r = call('GET', '/api/v1/auth/me', token=accTok)
accMe = r.get('data') or {}
print('     受理员权限：%s' % accMe.get('permissions'))
chk('⭐ 受理员权限为2条', len(accMe.get('permissions') or []) == 2,
    len(accMe.get('permissions') or []))
chk('受理员非管理员', accMe.get('admin') in (False, 'false'), accMe.get('admin'))

# 有权限：iam:user:list
st, r = call('GET', '/api/v1/rbac/users', token=accTok)
chk('⭐ 有权限可查用户列表', st == 200 and r.get('code') == 'BP00000',
    'http=%s code=%s' % (st, r.get('code')))

# 无权限：iam:user:create
st, r = call('POST', '/api/v1/rbac/users',
             {'username': 'hack' + sfx, 'password': 'x', 'realName': '非法'},
             token=accTok)
chk('⭐⭐ 无权限创建用户 → 403', st == 403, 'http=%s code=%s' % (st, r.get('code')))
chk('返回码 BP20002（无权限）', r.get('code') == 'BP20002', r.get('code'))
print('     拒绝信息：%s' % r.get('message'))
chk('拒绝信息指明缺少的权限', 'iam:user:create' in str(r.get('message')), r.get('message'))

# ---------- 7. 管理员可创建用户 ----------
st, r = call('POST', '/api/v1/rbac/users',
             {'username': 'staff' + sfx, 'password': 'pwd123456',
              'realName': '新建员工', 'userType': 'STAFF'}, token=adminTok)
chk('⭐⭐ 管理员可创建用户', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
newUid = (r.get('data') or {}).get('id')
chk('返回体不含密码哈希', (r.get('data') or {}).get('passwordHash') is None,
    (r.get('data') or {}).get('passwordHash'))

# 新用户登录（验证密码哈希生效）
st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'staff' + sfx, 'password': 'pwd123456'})
chk('⭐⭐ 新建用户可登录（密码哈希正确）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
newTok = (r.get('data') or {}).get('token')
st, r = call('GET', '/api/v1/auth/me', token=newTok)
chk('新用户无角色 → 权限为空', len((r.get('data') or {}).get('permissions') or []) == 0,
    (r.get('data') or {}).get('permissions'))

# ---------- 8. 分配角色后权限生效 ----------
st, r = call('GET', '/api/v1/rbac/roles', token=adminTok)
roles = r.get('data') or []
accRole = next((x for x in roles if x.get('roleCode') == 'ACCEPTOR'), None)
chk('可查角色列表', len(roles) >= 5, len(roles))
chk('★ 找到受理岗角色', accRole is not None, [x.get('roleCode') for x in roles])

if accRole:
    st, r = call('POST', '/api/v1/rbac/users/%s/roles' % newUid,
                 {'ids': [accRole['id']]}, token=adminTok)
    chk('⭐ 分配角色', (r.get('data') or 0) >= 1, r.get('data'))
    st, r = call('GET', '/api/v1/auth/me', token=newTok)
    chk('⭐⭐ 分配后权限立即生效', len((r.get('data') or {}).get('permissions') or []) == 2,
        (r.get('data') or {}).get('permissions'))

# ---------- 9. 登出后令牌失效 ----------
st, r = call('POST', '/api/v1/auth/logout', token=newTok)
chk('登出成功', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/auth/me', token=newTok)
chk('⚡ 登出后令牌立即失效 → 401', st == 401, st)

# ---------- 10. 单设备登录（踢旧会话）----------
st, r = call('POST', '/api/v1/auth/login', {'tenantId': TENANT, 'username': 'viewer', 'password': 'view123'})
v1 = (r.get('data') or {}).get('token')
st, r = call('POST', '/api/v1/auth/login', {'tenantId': TENANT, 'username': 'viewer', 'password': 'view123'})
v2 = (r.get('data') or {}).get('token')
st, r = call('GET', '/api/v1/auth/me', token=v1)
chk('⭐ 旧令牌仍有效（单设备默认关闭）', st == 200, st)

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
