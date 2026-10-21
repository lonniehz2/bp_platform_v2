# -*- coding: utf-8 -*-
"""核对各模块列表返回结构与真实条数"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None


def call(m, p):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    r = urllib.request.Request(BASE + p, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return -1, {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login') if False else None
req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']

for name, path in (('投诉', '/api/v1/complaints'), ('告警', '/api/v1/alerts'),
                   ('信用', '/api/v1/credits'), ('申诉', '/api/v1/appeals'),
                   ('工单', '/api/v1/workorders'), ('换房', '/api/v1/exchanges'),
                   ('钥匙包', '/api/v1/keyring')):
    st, r = call('GET', '%s?pageNum=1&pageSize=5' % path)
    d = r.get('data')
    if isinstance(d, dict):
        n, shape = d.get('total'), 'PageResult'
        n = int(n) if n is not None else len(d.get('rows') or [])
    elif isinstance(d, list):
        n, shape = len(d), 'List'
    else:
        n, shape = 0, str(type(d).__name__)
    print('  %-6s %-10s %-4s %s' % (name, shape, n, r.get('code')))
