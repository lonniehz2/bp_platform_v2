# -*- coding: utf-8 -*-
"""补造：换房（换第二个房源）+ 钥匙包（查真实 DTO 名）"""
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
PERSON = D['persons'][0]
HS = [h for h in D.get('houses', []) if h]
CS = D.get('contracts') or []


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


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

# ---------- 1) 换房：old→new 不同房源 ----------
print('■ 换房')
if len(HS) >= 2 and CS:
    st, r = call('POST', '/api/v1/exchanges', {
        'personId': PERSON, 'oldContractId': CS[0]['id'],
        'oldHouseId': CS[0]['houseId'], 'newHouseId': HS[-1],
        'exchangeType': 'VOLUNTARY', 'exchangeReason': '家庭人口增加需要更大户型',
        'exchangeReasonCode': 'FAMILY_GROW', 'familySizeBefore': 2,
        'familySizeAfter': 3, 'forceExchange': False})
    print('  %s %s %s' % (st, r.get('code'), str(r.get('message'))[:70]))
    st, r = call('GET', '/api/v1/exchanges?pageNum=1&pageSize=5')
    print('  换房单：%s 条' % len((r.get('data') or {}).get('rows') or []))

# ---------- 2) 钥匙包：找真实 DTO ----------
print('\n■ 钥匙包 DTO 搜索')
cand = []
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        if '@RequestMapping("/api/v1/keyring")' in s:
            for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
                print('  ■ %s(%s)' % (mm.group(1),
                                     re.sub(r'\s+', ' ', mm.group(2))[:140]))
                cand.append((mm.group(1), mm.group(2)))
            # 也可能用独立 DTO 类
            for mm in re.finditer(r'@RequestBody\s+(\w+)\s+(\w+)', s):
                print('  → @RequestBody %s' % mm.group(1))
                cand.append((mm.group(1), None))

for name, body in cand:
    if body:
        continue
    for root, _, files in os.walk(JAVA):
        if name + '.java' in files:
            s = io.open(os.path.join(root, name + '.java'), encoding='utf-8').read()
            m = re.search(r'record\s+' + name + r'\s*\((.*?)\)', s, re.S)
            if m:
                print('  ■ %s 字段：%s' % (name, re.sub(r'\s+', ' ', m.group(1))[:200]))
