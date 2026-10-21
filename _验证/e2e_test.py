# -*- coding: utf-8 -*-
"""
端到端功能验证（真实数据库 + 真实 HTTP）
场景：小区(bp_iam_org) → 楼栋 → 单元 → 楼层 → 房间 → 查整棵树
附带负向测试：楼栋下直接建房间应被拒绝
"""
import json
import sys
import time
import urllib.error
import urllib.request

import os
BASE = os.environ.get('BP_BASE_URL', 'http://127.0.0.1:18080')
TENANT = '350600'
HDR = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT, 'X-User-Id': '1001'}

passed = failed = 0


def call(method, path, body=None, expect_http=200):
    url = BASE + path
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HDR, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode('utf-8')
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8')
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {'raw': raw}


def check(name, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  [PASS] %s' % name)
    else:
        failed += 1
        print('  [FAIL] %s   %s' % (name, detail))


def digits_to_str(o):
    """服务端把 Long 序列化为字符串，这里统一为 str 便于比较"""
    return str(o)


print('=' * 74)
print(' 端到端功能验证（真实 DB + 真实 HTTP）')
print('=' * 74)

# ---------- 0) 服务健康 ----------
st, body = call('GET', '/actuator/health')
check('服务健康检查', st == 200 and body.get('status') == 'UP', str(body))

# ---------- 1) 建小区（bp_iam_org）----------
st, body = call('POST', '/api/v1/orgs', {
    'orgCode': 'E2E-ZZ01',
    'orgName': '端到端验证小区',
    'orgType': 'COMMUNITY',
    'address': '福建省漳州市测试路 1 号',
    'sortNo': 1,
})
ok = st == 200 and body and body.get('code') == 'BP00000'
check('创建小区', ok, str(body)[:200])
if not ok:
    print('\n  无法继续，终止。')
    sys.exit(1)
org_id = digits_to_str(body['data']['id'])
print('        小区ID = %s' % org_id)

# ---------- 2) 建楼栋 ----------
st, body = call('POST', '/api/v1/spaces', {
    'orgId': org_id, 'parentId': None, 'spaceCode': 'E2E-B01',
    'spaceName': '1幢', 'spaceType': 'BUILDING', 'sortNo': 1,
})
ok = st == 200 and body.get('code') == 'BP00000'
check('创建楼栋', ok, str(body)[:200])
bld_id = digits_to_str(body['data']['id']) if ok else None
if ok:
    d = body['data']
    check('楼栋 level=2 且 path_code=01/', d['spaceLevel'] == 2 and d['pathCode'] == '01/',
          'level=%s path=%s' % (d['spaceLevel'], d['pathCode']))

# ---------- 3) 负向：楼栋下直接建房间应失败 ----------
st, body = call('POST', '/api/v1/spaces', {
    'orgId': org_id, 'parentId': bld_id, 'spaceCode': 'E2E-BAD',
    'spaceName': '非法房间', 'spaceType': 'ROOM', 'sortNo': 1,
})
check('⭐ 楼栋下建房间被拒绝', body.get('code') == 'BP40001',
      'code=%s msg=%s' % (body.get('code'), body.get('message')))

# ---------- 4) 建单元 ----------
st, body = call('POST', '/api/v1/spaces', {
    'orgId': org_id, 'parentId': bld_id, 'spaceCode': 'E2E-B01-U01',
    'spaceName': '1单元', 'spaceType': 'UNIT', 'sortNo': 1,
})
ok = st == 200 and body.get('code') == 'BP00000'
check('创建单元', ok, str(body)[:200])
unit_id = digits_to_str(body['data']['id']) if ok else None

# ---------- 5) 建楼层 ----------
st, body = call('POST', '/api/v1/spaces', {
    'orgId': org_id, 'parentId': unit_id, 'spaceCode': 'E2E-B01-U01-F01',
    'spaceName': '1层', 'spaceType': 'FLOOR', 'sortNo': 1,
})
ok = st == 200 and body.get('code') == 'BP00000'
check('创建楼层', ok, str(body)[:200])
floor_id = digits_to_str(body['data']['id']) if ok else None

# ---------- 6) 建房间 ----------
st, body = call('POST', '/api/v1/spaces', {
    'orgId': org_id, 'parentId': floor_id, 'spaceCode': 'E2E-101',
    'spaceName': '101室', 'spaceType': 'ROOM', 'sortNo': 1, 'area': 58.5,
})
ok = st == 200 and body.get('code') == 'BP00000'
check('创建房间', ok, str(body)[:200])
if ok:
    d = body['data']
    check('房间 level=5', d['spaceLevel'] == 5, 'level=%s' % d['spaceLevel'])
    check('房间 path_code=01/01/01/01/', d['pathCode'] == '01/01/01/01/', 'path=%s' % d['pathCode'])
    check('full_name 已拼接', '1幢' in (d['fullName'] or '') and '101室' in (d['fullName'] or ''),
          'fullName=%s' % d['fullName'])

# ---------- 7) 查整棵树 ----------
st, body = call('GET', '/api/v1/spaces/tree?orgId=' + org_id)
ok = st == 200 and body.get('code') == 'BP00000'
tree = body.get('data') if ok else None
check('查询空间树', ok and isinstance(tree, list) and len(tree) == 1, str(body)[:200])
if ok and tree:
    root = tree[0]
    depth = 0
    cur = root
    chain = [root['spaceName']]
    while cur.get('children'):
        cur = cur['children'][0]
        chain.append(cur['spaceName'])
        depth += 1
    check('树深度为 4（楼栋→单元→楼层→房间）', depth == 3, 'depth=%d' % depth)
    print('        树: ' + ' → '.join(chain))

# ---------- 8) 负向：床位下不能建子节点 ----------
st, body = call('POST', '/api/v1/spaces', {
    'orgId': org_id, 'parentId': floor_id, 'spaceCode': 'E2E-X',
    'spaceName': 'X', 'spaceType': 'BUILDING', 'sortNo': 1,
})
check('楼层下建楼栋被拒绝', body.get('code') == 'BP40001',
      'code=%s' % body.get('code'))

# ---------- 9) 房源分页接口可用 ----------
st, body = call('GET', '/api/v1/houses?pageNum=1&pageSize=10')
check('房源分页接口可用', st == 200 and body.get('code') == 'BP00000', str(body)[:200])

# ---------- 10) 小区重复编码应拒绝 ----------
st, body = call('POST', '/api/v1/orgs', {
    'orgCode': 'E2E-ZZ01', 'orgName': '重复', 'orgType': 'COMMUNITY',
})
check('重复组织编码被拒绝', body.get('code') == 'BP30002',
      'code=%s' % body.get('code'))

# ---------- 11) 参数校验 ----------
st, body = call('POST', '/api/v1/orgs', {'orgCode': 'X', 'orgName': 'Y', 'orgType': 'BAD'})
check('非法 orgType 被拒绝', body.get('code') == 'BP10001', 'code=%s' % body.get('code'))

print()
print('-' * 74)
print(' 通过 %d / 失败 %d' % (passed, failed))
print('-' * 74)
sys.exit(0 if failed == 0 else 1)
