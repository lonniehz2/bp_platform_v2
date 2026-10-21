# -*- coding: utf-8 -*-
"""按路径自动发现创建接口与 DTO，造数（合同变更/规则集/开放应用/政务/对账）"""
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


def all_java():
    for root, _, files in os.walk(JAVA):
        for f in files:
            if f.endswith('.java'):
                yield os.path.join(root, f)


def rec_fields(name):
    for p in all_java():
        if os.path.basename(p) != name + '.java':
            continue
        s = io.open(p, encoding='utf-8').read()
        m = re.search(r'record\s+' + name + r'\s*\((.*?)\)\s*(?:\{|implements)', s, re.S)
        if m:
            return re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
    return None


def parse(body):
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
    b = rec_fields(name)
    if b is None:
        return None, []
    fs = parse(b)
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
            p[n] = 5625.00
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
                                                      'desc', 'title', 'name', 'info'))
                    else 'TEST')
    if over:
        p.update(over)
    return p, fs


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

# 找出这些 base path 的创建接口
WANT = ['contract-changes', 'rules/rulesets', 'open/apps', 'gov/adapters',
        'gov/reports']
found = {}
for p in all_java():
    if not p.endswith('Controller.java'):
        continue
    s = io.open(p, encoding='utf-8').read()
    bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
    if not bm:
        continue
    base = bm.group(1).replace('/api/v1', '').strip('/')
    if base not in WANT:
        continue
    for mm in re.finditer(r'@PostMapping(?:\(\s*"([^"]*)"\s*\))?[\s\S]{0,300}?'
                          r'@RequestBody(?:\s+@\w+)*\s+(\w+)\s+\w+', s):
        sub = mm.group(1) or ''
        found[base] = ('/api/v1/' + base + ('/' + sub if sub else ''), mm.group(2))
        break

print('=' * 72)
for base in WANT:
    if base not in found:
        print('□ %-16s 未找到带 @RequestBody 的创建接口' % base)
        continue
    path, dto = found[base]
    body, fs = build(dto)
    if body is None:
        print('□ %-16s DTO %s 字段未解析' % (base, dto))
        continue
    st, r = call('POST', path, body)
    print('■ %-16s → %s %s' % (base, r.get('code'), str(r.get('message'))[:60]))
    if r.get('code') != 'BP00000':
        print('   %s' % ', '.join(n for _, n, _ in fs)[:200])
