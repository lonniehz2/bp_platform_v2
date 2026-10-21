# -*- coding: utf-8 -*-
"""用真实接口验证报表枚举中文化"""
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
            return json.loads(x.read().decode())
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

print('=' * 66)
for code in ('HOUSE_LEDGER', 'CONTRACT_LEDGER', 'ARREARS_LEDGER'):
    r = call('POST', '/api/v1/rpt/reports/query',
             {'reportCode': code, 'pageNum': 1, 'pageSize': 5})
    d = r.get('data') or {}
    rows = d.get('rows') or []
    print('\n■ %-16s %s  共 %s 行' % (code, r.get('code'), d.get('total')))
    cols = [c.get('key') for c in (d.get('columns') or [])]
    print('   列：%s' % cols)
    if rows:
        print('   首行：%s' % json.dumps(rows[0], ensure_ascii=False)[:190])
        for c in cols:
            vals = sorted({str(x.get(c)) for x in rows})
            if any(v and v not in ('None',) for v in vals):
                print('     %-15s %s' % (c, vals[:6]))

# 导出任务 → CSV 内容
print('\n■ 异步导出')
r = call('POST', '/api/v1/rpt/exports',
         {'reportCode': 'HOUSE_LEDGER', 'pageSize': 5})
tid = (r.get('data') or {}).get('id')
print('   创建任务：%s id=%s' % (r.get('code'), tid))
if tid:
    call('POST', '/api/v1/rpt/exports/run-pending')
    c = call('GET', '/api/v1/rpt/exports/%s/content' % tid)
    txt = c.get('data') if isinstance(c.get('data'), str) else None
    if txt:
        for ln in [x for x in txt.split('\n') if x.strip()][:4]:
            print('   ' + ln[:140])
    else:
        print('   内容：%s %s' % (c.get('code'), str(c.get('message'))[:60]))
