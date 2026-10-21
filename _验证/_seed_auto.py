# -*- coding: utf-8 -*-
"""按 DTO 字段自动构造请求体，为 6 个空模块造测试数据"""
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


def find_record(name):
    for root, _, files in os.walk(JAVA):
        for f in files:
            if not f.endswith('.java'):
                continue
            s = io.open(os.path.join(root, f), encoding='utf-8').read()
            m = re.search(r'record\s+' + name + r'\s*\((.*?)\)\s*(?:\{|implements)', s, re.S)
            if m:
                return s, re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
    return None, None


def parse_fields(body):
    """返回 [(type, name, pattern)]"""
    out = []
    pending_pattern = None
    for ln in body.split('\n'):
        t = ln.strip()
        pm = re.search(r'regexp\s*=\s*"([^"]+)"', t)
        if pm:
            pending_pattern = pm.group(1)
        t2 = re.sub(r'^@\w+(\([^)]*\))?\s*', '', t).strip().rstrip(',')
        if not t2 or t2.startswith('//'):
            continue
        m = re.match(r'^(Long|Integer|String|BigDecimal|Boolean|LocalDate|LocalDateTime|'
                     r'List<Long>)\s+(\w+)$', t2)
        if m:
            out.append((m.group(1), m.group(2), pending_pattern))
            pending_pattern = None
    return out


def val(typ, name, pattern, idx=0):
    if pattern:
        opts = [x for x in pattern.replace('^$|', '').split('|') if x]
        if opts:
            return opts[min(idx, len(opts) - 1)]
    if typ == 'Long':
        if 'ouse' in name:
            return HOUSE
        if 'ontract' in name:
            return CONTRACT
        if 'erson' in name:
            return PERSON
        if 'rg' in name:
            return ORG
        return 1
    if typ == 'Integer':
        return 1
    if typ == 'BigDecimal':
        return 100.0
    if typ == 'Boolean':
        return False
    if typ == 'LocalDate':
        return '2026-01-01'
    if typ == 'LocalDateTime':
        return '2026-01-01 00:00:00'
    if typ == 'List<Long>':
        return [HOUSE] if HOUSE else []
    lname = name.lower()
    if 'reason' in lname or 'content' in lname:
        return '自动生成的测试数据'
    if 'phone' in lname:
        return '13800138000'
    if 'name' in lname:
        return '测试名称'
    return 'TEST'


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

TASKS = [
    ('投诉', 'ComplaintCreateCmd', '/api/v1/complaints'),
    ('告警', 'AlertCreateCmd', '/api/v1/alerts'),
    ('钥匙包', 'KeyringCreateCmd', '/api/v1/keyring'),
    ('信用惩戒', 'CreditCreateCmd', '/api/v1/credits'),
    ('申诉', 'AppealCreateCmd', '/api/v1/appeals'),
    ('工单', 'WorkOrderCreateCmd', '/api/v1/workorders'),
    ('换房', 'ExchangeCreateCmd', '/api/v1/exchanges'),
]

print('=' * 70)
print(' 自动构造并提交测试数据')
print('=' * 70)
for label, rec, path in TASKS:
    s, body = find_record(rec)
    if body is None:
        print('\n■ %s（%s 未找到 record）' % (label, rec))
        continue
    fields = parse_fields(body)
    payload = {n: val(t, n, p) for (t, n, p) in fields}
    st, r = call('POST', path, payload)
    print('\n■ %s  %s' % (label, path))
    print('   字段 %d：%s' % (len(fields), ', '.join(n for _, n, _ in fields)))
    print('   结果 %s %s %s' % (st, r.get('code'),
                               str(r.get('message'))[:80]))
    if r.get('code') != 'BP00000':
        print('   请求体：%s' % json.dumps(payload, ensure_ascii=False)[:300])
