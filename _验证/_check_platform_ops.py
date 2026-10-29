# -*- coding: utf-8 -*-
"""平台运营台回归：登录、创建、管理员登录、停用拦截、归档。"""
import json
import urllib.error
import urllib.request

B = 'http://192.168.31.11:8080/api/v1'


def call(p, m='GET', body=None, token=None, tenant='350600'):
    d = json.dumps(body).encode() if body is not None else (b'' if m == 'POST' else None)
    h = {'Content-Type': 'application/json'}
    if token:
        h['X-Operator-Token'] = token
    else:
        h['X-Tenant-Id'] = tenant
    x = urllib.request.Request(B + p, data=d, method=m, headers=h)
    try:
        y = urllib.request.urlopen(x, timeout=60)
        return y.status, json.loads(y.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'message': 'HTTP ' + str(e.code)}


st, r = call('/platform-admin/auth/login', 'POST',
             {'username': 'opsadmin', 'password': 'Ops@123456'})
print('运营登录', st, r.get('message'))
tok = (r.get('data') or {}).get('token')
if tok:
    st, r = call('/platform-admin/platforms', token=tok)
    print('平台列表', st, '数量', len(r.get('data') or []))
    st, r = call('/platform-admin/platforms', 'POST', {
        'tenantName': '联调测试平台', 'regionCode': '350699', 'tenantType': 'GOV',
        'contactName': '测试', 'contactPhone': '13900000000',
        'adminUsername': 'testadmin', 'adminRealName': '平台管理员'
    }, tok)
    print('创建平台', st, r.get('message'))
    d = r.get('data') or {}
    code = (d.get('platform') or {}).get('tenantCode')
    pwd = d.get('initialPassword')
    pid = (d.get('platform') or {}).get('id')
    print('  编码', code, '初始密码', pwd)
    if code and pwd:
        st, r2 = call('/auth/login', 'POST',
                      {'tenantId': code, 'username': 'testadmin', 'password': pwd},
                      tenant=code)
        print('平台管理员登录', st, r2.get('message'))
        if pid:
            st, r3 = call('/platform-admin/platforms/%s/disable' % pid, 'POST', {}, tok)
            st, r4 = call('/auth/login', 'POST',
                          {'tenantId': code, 'username': 'testadmin', 'password': pwd},
                          tenant=code)
            print('停用后登录', st, r4.get('message'))
            st, r5 = call('/platform-admin/platforms/%s/admins' % pid, token=tok)
            print('管理员数量', st, len(r5.get('data') or []))
            st, r6 = call('/platform-admin/platforms/%s/archive' % pid, 'POST', {}, tok)
            print('归档', st, r6.get('message'))
