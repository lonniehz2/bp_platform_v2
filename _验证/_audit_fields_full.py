# -*- coding: utf-8 -*-
"""全面审计字段中文名覆盖：列表(全部行) + 详情接口"""
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


def get(p):
    r = urllib.request.Request(BASE + p, headers={
        'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600'})
    try:
        with urllib.request.urlopen(r, timeout=45) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__}


labels = get('/api/v1/sys/field-labels').get('data') or {}
print('远程字典 %d 个字段' % len(labels))

# 前端静态字典
import io
import re
FE = r'D:\Work\业务平台开发\frontend\src\constants\fieldLabels.js'
fs = io.open(FE, encoding='utf-8').read()
static = set(re.findall(r'^\s{2}(\w+):\s*[\'"]', fs, re.M))
print('前端静态字典 %d 个字段' % len(static))

LIST = ['/applications', '/contracts', '/contract-changes', '/allocation/batches',
        '/allocation/allocations', '/allocation/waiting', '/annual-reviews',
        '/terminations', '/fin/bills', '/fin/payments', '/fin/deposits',
        '/fin/refunds', '/fin/subsidies/records', '/fin/dunnings',
        '/fin/cash-flows', '/fin/fee-items', '/workorders', '/alerts',
        '/complaints', '/appeals', '/credits', '/exchanges', '/visits',
        '/short-rent-orders', '/access-records', '/keyring', '/grants',
        '/publicities', '/devices', '/orgs', '/houses', '/persons',
        '/house-calendar', '/fin/reconciles', '/rpt/reports']

DETAIL = ['/short-rent-orders', '/applications', '/contracts', '/fin/bills',
          '/fin/payments', '/fin/deposits', '/fin/refunds', '/workorders',
          '/terminations', '/annual-reviews', '/alerts', '/appeals',
          '/credits', '/exchanges', '/complaints', '/visits', '/keyring',
          '/grants', '/publicities', '/devices', '/persons', '/houses']

SKIP = {'id', 'tenantId'}


def collect(rows, seen, where):
    for row in rows:
        if not isinstance(row, dict):
            continue
        for k in row:
            if k.endswith('Label') or k.endswith('Name') or k in SKIP:
                continue
            seen.setdefault(k, set()).add(where)


missing = {}
allkeys = set()

# 列表：取全部行
for path in LIST:
    sep = '&' if '?' in path else '?'
    data = get('/api/v1%s%spageNum=1&pageSize=20' % (path, sep)).get('data')
    rows = (data.get('rows') if isinstance(data, dict) else data) or []
    allkeys.update(k for r in rows if isinstance(r, dict) for k in r)
    collect(rows, missing, path.split('/')[-1])

# 详情：取首条 id
for path in DETAIL:
    sep = '&' if '?' in path else '?'
    data = get('/api/v1%s%spageNum=1&pageSize=1' % (path, sep)).get('data')
    rows = (data.get('rows') if isinstance(data, dict) else data) or []
    if not rows or not isinstance(rows[0], dict):
        continue
    rid = rows[0].get('id')
    if not rid:
        continue
    d = get('/api/v1%s/%s' % (path, rid)).get('data')
    if isinstance(d, dict):
        allkeys.update(d.keys())
        collect([d], missing, path.split('/')[-1] + '/详情')

print('实际出现字段（去 Label/Name）%d 个' % len(allkeys))

gap = {}
for k, where in missing.items():
    if k not in labels and k not in static:
        gap[k] = where

print('\n■ 字典未覆盖：%d 个' % len(gap))
lines = []
for k in sorted(gap):
    print('   %-24s %s' % (k, ', '.join(sorted(gap[k]))[:56]))
    # 生成建议名：驼峰拆词
    lines.append("  %s: '%s'," % (k, k))

io.open(r'D:\Work\业务平台开发\_验证\_missing_fields.txt', 'w',
        encoding='utf-8').write('\n'.join(sorted(gap)))
print('\n缺口清单已写入 _missing_fields.txt')
