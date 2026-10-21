# -*- coding: utf-8 -*-
"""补造钥匙包（KeyringCmd 真实字段）+ 汇总本轮数据"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
PERSON = D['persons'][0]


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


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

print('■ 钥匙包（KeyringCmd: personId/keyType/keyAlias/channelValue/...）')
for kt, cv in (('FACE', 'face.person.001'), ('CARD', 'card:8899'), ('QRCODE', 'qr:7701')):
    st, r = call('POST', '/api/v1/keyring', {
        'personId': PERSON, 'keyType': kt, 'keyAlias': kt + '测试钥匙',
        'channelValue': cv, 'keySource': 'PLATFORM',
        'verifyWay': 'PLATFORM', 'syncScope': 'HOUSE_DOOR',
        'expireTime': '2027-12-31 23:59:59'})
    print('  %s %s → %s %s' % (kt, st, r.get('code'), str(r.get('message'))[:56]))

print('\n■ 汇总各模块数据量')
for name, path in (('投诉', '/complaints'), ('告警', '/alerts'), ('信用', '/credits'),
                   ('申诉', '/appeals'), ('工单', '/workorders'),
                   ('换房', '/exchanges'), ('钥匙包', '/keyring')):
    st, r = call('GET', '%s?pageNum=1&pageSize=5' % path if path != '/keyring'
                 else '/keyring?pageNum=1&pageSize=5')
    d = r.get('data') or {}
    print('  %-6s %s 条' % (name, d.get('total')))
