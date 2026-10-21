# -*- coding: utf-8 -*-
"""造数：合同变更/规则集/开放应用/政务适配器→报送/财务对账"""
import io
import json
import os
import re
import urllib.error
import urllib.request

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
BASE = 'http://192.168.31.11:8080'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']
PERSON = D['persons'][0]
CONTRACT = (D.get('contracts') or [{}])[0].get('id')
HOUSE = (D.get('houses') or [None])[0]


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


def rec(name):
    for root, _, files in os.walk(JAVA):
        if name + '.java' not in files:
            continue
        s = io.open(os.path.join(root, name + '.java'), encoding='utf-8').read()
        m = re.search(r'record\s+' + name + r'\s*\((.*?)\)\s*(?:\{|implements)', s, re.S)
        if m:
            return re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
    return None


def fields(body):
    out, pat = [], None
    for ln in body.split('\n'):
        t = ln.strip()
        pm = re.search(r'regexp\s*=\s*"([^"]+)"', t)
        if pm:
            pat = pm.group(1)
        t2 = re.sub(r'^@\w+(\([^)]*\))?\s*', '', t).strip().rstrip(',')
        if not t2 or t2.startswith('//'):
            continue
        m = re.match(r'^(Long|Integer|String|BigDecimal|Boolean|LocalDate|LocalDateTime|'
                     r'List<Long>)\s+(\w+)$', t2)
        if m:
            out.append((m.group(1), m.group(2), pat))
            pat = None
    return out


def build(name, over=None):
    body = rec(name)
    if body is None:
        return None, []
    fs = fields(body)
    p = {}
    for t, n, pa in fs:
        ln = n.lower()
        if pa:
            opts = [x for x in pa.replace('^$|', '').split('|') if x]
            p[n] = opts[0] if opts else 'TEST'
        elif t == 'Long':
            p[n] = (CONTRACT if 'ontract' in ln else PERSON if 'erson' in ln
                    else HOUSE if 'ouse' in ln else ORG if 'rg' in ln else 1)
        elif t == 'Integer':
            p[n] = 1
        elif t == 'BigDecimal':
            p[n] = 100.0
        elif t == 'Boolean':
            p[n] = False
        elif t == 'LocalDate':
            p[n] = '2026-11-01'
        elif t == 'LocalDateTime':
            p[n] = '2026-11-01 00:00:00'
        elif t == 'List<Long>':
            p[n] = [HOUSE] if HOUSE else []
        else:
            p[n] = ('自动测试' if any(k in ln for k in ('reason', 'content', 'remark',
                                                      'desc', 'title', 'name'))
                    else 'TEST')
    if over:
        p.update(over)
    return p, fs


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

TRIES = [
    ('合同变更', 'ContractChangeCreateCmd', '/api/v1/contract-changes'),
    ('规则集', 'RulesetCreateCmd', '/api/v1/rules/rulesets'),
    ('开放应用', 'OpenAppCreateCmd', '/api/v1/open/apps'),
    ('政务适配器', 'AdapterCreateCmd', '/api/v1/gov/adapters'),
    ('政务适配器2', 'GovAdapterCreateCmd', '/api/v1/gov/adapters'),
]

print('=' * 72)
for label, dto, path in TRIES:
    body, fs = build(dto)
    if body is None:
        print('□ %-12s %s 未找到' % (label, dto))
        continue
    st, r = call('POST', path, body)
    print('■ %-12s %s → %s %s' % (label, path, r.get('code'),
                                  str(r.get('message'))[:60]))
    if r.get('code') != 'BP00000':
        print('   字段：%s' % ', '.join(n for _, n, _ in fs))
        print('   body：%s' % json.dumps(body, ensure_ascii=False)[:200])

# 财务对账：尝试生成
print('\n■ 财务对账生成')
for p in ('/api/v1/fin/reconciles/generate', '/api/v1/fin/reconciles'):
    st, r = call('POST', p, {'orgId': ORG, 'bizDate': '2026-11-01'})
    print('  POST %-36s %s %s' % (p.replace('/api/v1', ''), r.get('code'),
                                  str(r.get('message'))[:50]))
