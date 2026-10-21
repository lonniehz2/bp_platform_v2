# -*- coding: utf-8 -*-
"""查人员列表 keyword 的匹配行为"""
import json
import urllib.request

BASE = 'http://192.168.31.11:8080'


def call(path, method='GET', body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Tenant-Id', '350600')
    if token:
        req.add_header('Authorization', 'Bearer ' + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


st, d = call('/api/v1/auth/login', 'POST',
             {'tenantCode': '350600', 'username': 'admin', 'password': 'admin123'})
tok = (d.get('data') or {}).get('token')

# 最近创建的人员（按 id 倒序首页第一条）
st, pd = call('/api/v1/persons?pageNum=1&pageSize=3', 'GET', None, tok)
rows = ((pd.get('data') or {}).get('rows') or [])
print('首页人员：', [(r.get('personName'), r.get('phone'), r.get('id')) for r in rows])

target = rows[0].get('personName') if rows else ''
print('\n用 keyword=%r 查询：' % target)
st, kd = call('/api/v1/persons?pageNum=1&pageSize=5&keyword=' + urllib.parse.quote(target),
              'GET', None, tok)
krows = ((kd.get('data') or {}).get('rows') or [])
print('  total=', (kd.get('data') or {}).get('total'),
      'rows=', [r.get('personName') for r in krows])

print('\n再查刚创建的 E2E 人员（前 3 条）：')
for r in rows:
    nm = r.get('personName') or ''
    if nm.startswith('E2E'):
        st, kd2 = call('/api/v1/persons?pageNum=1&pageSize=5&keyword=' + urllib.parse.quote(nm), 'GET', None, tok)
        print('  %-18s -> total=%s rows=%s' % (nm, (kd2.get('data') or {}).get('total'),
              [x.get('personName') for x in ((kd2.get('data') or {}).get('rows') or [])][:3]))
