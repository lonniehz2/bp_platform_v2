# -*- coding: utf-8 -*-
"""验证三类报表的枚举是否已中文化（含异步导出的 CSV 内容）"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=90) as x:
            ct = x.headers.get('Content-Type', '')
            raw = x.read().decode('utf-8', 'replace')
            return (json.loads(raw) if 'json' in ct or raw.strip().startswith('{')
                    else raw)
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')

for code, cols in (('HOUSE_LEDGER', ('houseType', 'houseStatus')),
                   ('CONTRACT_LEDGER', ('contractStatus',)),
                   ('ARREARS_LEDGER', ('billStatus',))):
    d = call('GET', '/api/v1/rpt/reports/%s/data?pageNum=1&pageSize=5' % code)
    data = d.get('data') or {}
    rows = data.get('rows') or []
    print('\n■ %s  共 %s 行' % (code, data.get('total')))
    for c in cols:
        vals = sorted({str(r.get(c)) for r in rows})
        print('   %-14s 值：%s' % (c, vals))
    if rows:
        print('   首行：%s' % json.dumps(rows[0], ensure_ascii=False)[:160])

# 异步导出任务的 CSV 内容
print('\n■ 异步导出 CSV 内容')
r = call('POST', '/api/v1/rpt/reports/HOUSE_LEDGER/export', {'pageSize': 5})
task = (r.get('data') or {}).get('id') or (r.get('data') or {}).get('taskNo')
print('   导出任务：%s' % r.get('code'))
tasks = call('GET', '/api/v1/rpt/reports/tasks?pageNum=1&pageSize=3')
tr = (tasks.get('data') or {}).get('rows') or []
if tr:
    tid = tr[0].get('id')
    content = call('GET', '/api/v1/rpt/reports/tasks/%s/content' % tid)
    if isinstance(content, str):
        lines = [x for x in content.split('\n') if x.strip()][:3]
        for ln in lines:
            print('   ' + ln[:150])
    else:
        print('   %s' % str(content)[:200])
