# -*- coding: utf-8 -*-
"""通用造数：自动发现模块的创建接口与其 DTO，构造请求体提交"""
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
ROOM = [r for r in D.get('rooms', []) if r]
ROOM = ROOM[0] if ROOM else None


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
            p = os.path.join(root, f)
            s = io.open(p, encoding='utf-8').read()
            m = re.search(r'record\s+' + name + r'\s*\((.*?)\)\s*(?:\{|implements)', s, re.S)
            if m:
                return re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
    return None


def parse_fields(body):
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


def val(typ, name, pat):
    if pat:
        opts = [x for x in pat.replace('^$|', '').split('|') if x]
        if opts:
            return opts[0]
    ln = name.lower()
    if typ == 'Long':
        if 'room' in ln or 'space' in ln:
            return ROOM
        if 'ouse' in ln:
            return HOUSE
        if 'ontract' in ln:
            return CONTRACT
        if 'erson' in ln:
            return PERSON
        if 'rg' in ln:
            return ORG
        return 1
    if typ == 'Integer':
        return 1
    if typ == 'BigDecimal':
        return 100.0
    if typ == 'Boolean':
        return False
    if typ == 'LocalDate':
        return '2026-11-01'
    if typ == 'LocalDateTime':
        return '2026-11-01 00:00:00'
    if typ == 'List<Long>':
        return [HOUSE] if HOUSE else []
    if 'reason' in ln or 'content' in ln or 'remark' in ln or 'desc' in ln:
        return '自动生成测试数据'
    if 'phone' in ln:
        return '13800138000'
    if 'code' in ln:
        return 'T' + str(abs(hash(name)) % 10000)
    if 'name' in ln or 'title' in ln:
        return '测试' + name
    if 'url' in ln:
        return 'https://example.com/a.pdf'
    if 'year' in ln:
        return '2026'
    return 'TEST'


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

# 目标模块（为空清单）
WANT = ['contract-changes', 'terminations', 'reconciles', 'rulesets',
        'messages', 'grants', 'grant-reconcile', 'open/apps', 'gov',
        'short-rent-orders']

print('=' * 74)
print(' 通用造数：自动发现创建接口 + DTO')
print('=' * 74)
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        p = os.path.join(root, f)
        s = io.open(p, encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if not bm:
            continue
        base = bm.group(1).replace('/api/v1', '').strip('/')
        if not any(base == w or base.startswith(w + '/') or w in base for w in WANT):
            continue
        # 第一个带 @RequestBody XxxCmd 的 POST
        m = re.search(r'@PostMapping(?:\(\s*"([^"]*)"\s*\))?\s*\n\s*public\s+[\w<>,\s\.\[\]]+'
                      r'\s+\w+\(([^)]*@RequestBody[^)]*)\)', s)
        if not m:
            continue
        sub = (m.group(1) or '')
        path = '/api/v1/' + base + ('/' + sub if sub else '')
        dm = re.search(r'@RequestBody\s+(?:@\w+\s+)*(\w+)\s+\w+', m.group(2))
        if not dm:
            continue
        dto = dm.group(1)
        body_src = find_record(dto)
        if body_src is None:
            print('\n■ %-28s DTO %s 未找到字段' % (base, dto))
            continue
        fields = parse_fields(body_src)
        payload = {n: val(t, n, pa) for (t, n, pa) in fields}
        st, r = call('POST', path, payload)
        print('\n■ %-26s %s' % (base, path))
        print('   %s %s %s' % (st, r.get('code'), str(r.get('message'))[:70]))
        if r.get('code') != 'BP00000':
            print('   body: %s' % json.dumps(payload, ensure_ascii=False)[:240])
