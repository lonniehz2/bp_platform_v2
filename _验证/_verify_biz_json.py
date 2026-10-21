# -*- coding: utf-8 -*-
"""biz 申请审核 · checkItems(JSON列) 落库验证"""
import json
import urllib.error
import urllib.parse
import urllib.request

BASE = 'http://192.168.31.11:8080'
H = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600', 'X-User-Id': '1001'}


def call(m, p, b=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=25) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


ok = fail = 0


def chk(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1
        print('  [PASS] ' + name)
    else:
        fail += 1
        print('  [FAIL] ' + name + '  ' + str(extra))


print('=' * 70)
print(' checkItems(JSON 列) 落库验证')
print('=' * 70)

st, r = call('POST', '/api/v1/applications', {
    'orgId': 7001, 'personId': 4001, 'securityType': 'PUBLIC', 'securityMode': 'HOUSE',
    'applyChannel': 'ONLINE', 'familySize': 2, 'declaredIncome': '8000',
    'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1})
aid = (r.get('data') or {}).get('id')
chk('提交申请', r.get('code') == 'BP00000', r.get('code'))

call('POST', '/api/v1/applications/%s/accept' % aid, {'userId': 9002})

q = '?userId=9001&userName=' + urllib.parse.quote('联审员')
items = json.dumps({'income': 'PASS', 'property': 'PASS', 'socialSecurity': 'PASS'},
                   ensure_ascii=False)
print('  发送 checkItems =', items)

st, r = call('POST', '/api/v1/applications/%s/review%s' % (aid, q), {
    'stage': 'JOINT', 'dept': 'REAL_ESTATE', 'result': 'PASS',
    'opinion': '三项核验通过', 'checkItems': items})
chk('带 checkItems 的审核提交', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('GET', '/api/v1/applications/%s/reviews' % aid)
recs = r.get('data') or []
print('  轨迹条数:', len(recs))
found = False
for x in recs:
    ci = x.get('checkItems') or ''
    print('    阶段=%s 部门=%s 结果=%s checkItems=%s'
          % (x.get('reviewStage'), x.get('reviewDept'), x.get('reviewResult'), ci[:70]))
    if 'property' in ci and 'income' in ci:
        found = True
chk('⭐ 核验项明细(JSON)完整留痕', found, recs)

# 校验非法 JSON 会被 MySQL 拒绝，说明列确实是 JSON 类型
st, r = call('POST', '/api/v1/applications/%s/review%s' % (aid, q), {
    'stage': 'FORM', 'result': 'PASS', 'opinion': 'x', 'checkItems': '{bad json}'})
chk('非法 JSON 被数据库拒绝（列确为 JSON 类型）',
    r.get('code') in ('BP99999',), r.get('code'))

print()
print('  通过 %d / 失败 %d' % (ok, fail))
