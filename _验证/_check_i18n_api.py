# -*- coding: utf-8 -*-
import json
import urllib.error
import urllib.request

B = 'http://192.168.31.11:8080/api/v1'


def call(path, method='GET', body=None, token=None, lang=None):
    data = json.dumps(body).encode() if body is not None else (b'' if method in ('POST', 'PUT') else None)
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if token:
        h['Authorization'] = 'Bearer ' + token
    if lang:
        h['Accept-Language'] = lang
    req = urllib.request.Request(B + path, data=data, method=method, headers=h)
    try:
        return urllib.request.urlopen(req, timeout=30).read().decode()
    except urllib.error.HTTPError as e:
        return 'HTTP%d %s' % (e.code, e.read().decode())


print('EN bad login:', call('/auth/login', 'POST',
                             {'tenantId': '350600', 'username': 'admin',
                              'password': 'wrong'}, lang='en-US')[:220])
print('ZH bad login:', call('/auth/login', 'POST',
                             {'tenantId': '350600', 'username': 'admin',
                              'password': 'wrong'}, lang='zh-CN')[:220])

r = json.loads(call('/auth/login', 'POST',
                    {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}))
tok = r['data']['token']
print('PUT locale:', call('/auth/locale', 'PUT', {'locale': 'en-US'}, tok))
me = json.loads(call('/auth/me', token=tok))
print('me.locale:', me['data'].get('locale'))
# 恢复中文，避免影响后续验收
print('restore:', call('/auth/locale', 'PUT', {'locale': 'zh-CN'}, tok))
me2 = json.loads(call('/auth/me', token=tok))
print('me.locale after restore:', me2['data'].get('locale'))
