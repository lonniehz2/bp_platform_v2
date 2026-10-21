# -*- coding: utf-8 -*-
"""按真实 DTO 建组织/空间/人员，并导出 HouseCreateCmd 字段"""
import io
import json
import os
import re
import time
import urllib.error
import urllib.request

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__, 'message': str(e)}


def show(r, tag):
    c = r.get('code')
    d = (r.get('data') or {}).get('id')
    print('  %s %-34s %s %s' % ('✓' if c == 'BP00000' else '✗', tag, c,
                                ('id=%s' % d) if d else str(r.get('message'))[:52]))
    return d


# 合法身份证（GB11643 校验位）
def make_id(seq=1, birth='19900101', area='350600'):
    body = '%s%s%03d' % (area, birth, seq)
    w = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    return body + '10X98765432'[sum(int(body[i]) * w[i] for i in range(17)) % 11]


TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'}
           ).get('data', {}).get('token')
print('登录：%s\n' % ('OK' if TOK else 'FAIL'))

sfx = str(int(time.time()))[-5:]
print('— 组织 —')
org_id = show(call('POST', '/api/v1/orgs', {
    'orgCode': 'TS' + sfx, 'orgName': '测试小区' + sfx, 'orgType': 'COMMUNITY',
    'sortNo': 1, 'remark': '自动生成的测试数据'}), '小区')

print('— 空间 —')
def sp(code, name, stype, parent):
    return show(call('POST', '/api/v1/spaces', {
        'orgId': org_id, 'parentId': parent, 'spaceCode': code,
        'spaceName': name, 'spaceType': stype, 'sortNo': 1}), '%s %s' % (stype, name))

b = sp('A' + sfx, '1号楼', 'BUILDING', org_id)
u = sp('A' + sfx + '01', '1单元', 'UNIT', b)
f = sp('A' + sfx + '0101', '1层', 'FLOOR', u)
rooms = []
for i in range(1, 6):
    rooms.append(sp('A%s0101%02d' % (sfx, i), '10%d室' % i, 'ROOM', f))

print('— 人员 —')
persons = []
for i in range(1, 6):
    pid = show(call('POST', '/api/v1/persons', {
        'personName': '测试租户%d' % i, 'idCard': make_id(seq=i * 7 + 3),
        'phone': '138%08d' % (10000000 + i * 1111), 'orgId': org_id,
        'householdType': 'URBAN'}), '人员%d' % i)
    persons.append(pid)

data = {'orgId': org_id, 'building': b, 'unit': u, 'floor': f,
        'rooms': rooms, 'persons': persons}
open(r'D:\Work\业务平台开发\_验证\_test_data.json', 'w', encoding='utf-8').write(
    json.dumps(data, ensure_ascii=False, indent=1))
print('\n已保存 _test_data.json：房间 %d / 人员 %d'
      % (len([r for r in rooms if r]), len([p for p in persons if p])))

# ---------- 导出 HouseCreateCmd 与 ContractCreateCmd 必填约束 ----------
print('\n=== HouseCreateCmd ===')
p = os.path.join(JAVA, 'asset', 'dto', 'HouseCreateCmd.java')
if os.path.exists(p):
    s = io.open(p, encoding='utf-8').read()
    m = re.search(r'record\s+HouseCreateCmd\s*\((.*?)\)\s*\{', s, re.S)
    if m:
        for ln in re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split('\n'):
            t = ln.strip().rstrip(',')
            if t:
                print('   ' + t[:110])
