# -*- coding: utf-8 -*-
"""信用禁申拦截验证：真实申请接口是否被拦住"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
H = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600', 'X-User-Id': '1001'}


def call(m, p, b=None):
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
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


sfx = str(int(time.time()))[-6:]
PID = 910000 + int(sfx) % 100000
print('=' * 78)
print(' 信用禁申 · 真实申请接口是否被拦住')
print('=' * 78)

st, r = call('POST', '/api/v1/orgs', {'orgCode': 'CRG-' + sfx, 'orgName': '信用拦截验证',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')


def mkapp(person_id, app_id):
    return call('POST', '/api/v1/applications', {
        'orgId': int(org), 'personId': person_id, 'securityType': 'PUBLIC',
        'securityMode': 'HOUSE', 'applyChannel': 'ONLINE', 'familySize': 3,
        'complianceCommitFlag': 1, 'dataShareAgreeFlag': 1,
        'declaredIncome': '5000', 'intentDistrict': '测试区'})


# ---------- 1. 干净人员可正常申请 ----------
st, r = mkapp(PID, 1)
chk('⭐ 无失信人员可正常申请', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
appId = (r.get('data') or {}).get('id')

# ---------- 2. 记入失信 ----------
st, r = call('POST', '/api/v1/credits', {
    'personId': PID, 'bizType': 'APPLICATION', 'bizId': int(appId) if appId else None,
    'violationType': 'FALSE_INFO',
    'violationDesc': '申报收入与实际不符，提供虚假收入证明',
    'sanctionType': 'BAN_APPLY', 'decideUserId': 9003,
    'legalDocNo': '漳住保决字〔2026〕第 012 号'})
chk('⭐ 记入失信（提供虚假信息）', r.get('code') == 'BP00000', r.get('code'))
cr = r.get('data') or {}
chk('严重违规限 5 年', str(cr.get('banYears')) == '5', cr.get('banYears'))
print('     限制期至：%s' % cr.get('banEndDate'))

# ---------- 3. ⭐⭐ 失信后再次申请 → 被真实拦住 ----------
st, r = mkapp(PID, 2)
chk('⭐⭐ 失信后申请被拒（真实申请接口）', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拒绝信息：%s' % r.get('message'))
chk('拒绝信息含违规类型', '提供虚假信息' in str(r.get('message')), r.get('message'))
chk('拒绝信息含解禁日期', '解禁日期' in str(r.get('message')), r.get('message'))

# ---------- 4. 校验在最前（不会因其它必填项缺失而掩盖）----------
st, r = call('POST', '/api/v1/applications', {
    'orgId': int(org), 'personId': PID, 'securityType': 'PUBLIC',
    'securityMode': 'HOUSE', 'applyChannel': 'ONLINE', 'familySize': 3,
    'complianceCommitFlag': 0, 'dataShareAgreeFlag': 0})
chk('⭐⭐ 信用校验优先于承诺书校验（先报禁申）',
    r.get('code') == 'BP40001' and '限制申请' in str(r.get('message')),
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 5. 他人不受影响 ----------
st, r = mkapp(PID + 1, 3)
chk('⭐ 其他人员不受影响', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 6. 撤销信用后恢复申请资格 ----------
st, r = call('GET', '/api/v1/credits/by-person/%s' % PID)
rows = r.get('data') or []
crId = rows[0].get('id') if rows else None
st, r = call('POST', '/api/v1/credits/%s/revoke' % crId, {'reason': '复议认定证据不足'})
chk('撤销信用记录', (r.get('data') or {}).get('status') == 'REVOKED', r.get('code'))

st, r = mkapp(PID, 4)
chk('⭐⭐ 撤销后可再次申请', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
