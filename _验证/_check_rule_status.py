# -*- coding: utf-8 -*-
"""查看计费规则状态与审批失败原因"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']
H = {'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600',
     'Content-Type': 'application/json'}

r = urllib.request.Request(BASE + '/api/v1/fin/billing-rules?pageNum=1&pageSize=3',
                           headers=H)
data = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())['data']
rows = data.get('rows') if isinstance(data, dict) else data
print('规则 %d 条' % len(rows))
for x in rows[:3]:
    print('  id=%s code=%s status=%s approveStatus=%s'
          % (x.get('id'), x.get('ruleCode'), x.get('ruleStatus'),
             x.get('approveStatus')))

if rows:
    rid = rows[0]['id']
    r2 = urllib.request.Request(BASE + '/api/v1/fin/billing-rules/%s/approve' % rid,
                                data=b'{}', method='POST', headers=H)
    try:
        print('审批：%s' % json.loads(urllib.request.urlopen(r2, timeout=30)
                                     .read().decode()).get('code'))
    except urllib.error.HTTPError as e:
        print('审批失败：%s %s' % (e.code, e.read().decode()[:200]))
