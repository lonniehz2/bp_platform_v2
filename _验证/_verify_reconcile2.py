# -*- coding: utf-8 -*-
"""补验：账实相符的对账不可处理"""
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
        with urllib.request.urlopen(r, timeout=30) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


ok = fail = 0


def chk(n, c, e=''):
    global ok, fail
    if c:
        ok += 1
        print('  [PASS] ' + n)
    else:
        fail += 1
        print('  [FAIL] ' + n + '  ' + str(e))


today = time.strftime('%Y-%m-%d')
print('=== 补验：账实相符的对账 ===')

st, r = call('POST', '/api/v1/fin/reconciles', {
    'reconcileDate': today, 'reconcileType': 'MANUAL',
    'systemAmount': '3000', 'channelAmount': '3000'})
d = r.get('data') or {}
rid = d.get('id')
print('     系统 %s 渠道 %s 差异 %s 状态 %s'
      % (d.get('systemAmount'), d.get('channelAmount'), d.get('diffAmount'),
         d.get('reconcileStatusLabel')))
chk('⭐ 金额相同 → 差异 0.00', str(d.get('diffAmount')) == '0.00', d.get('diffAmount'))
chk('⭐ 状态 MATCHED/一致', d.get('reconcileStatus') == 'MATCHED'
    and d.get('reconcileStatusLabel') == '一致', d.get('reconcileStatus'))
chk('matched=true', d.get('matched') in (True, 'true'), d.get('matched'))

st, r = call('POST', '/api/v1/fin/reconciles/%s/handle' % rid, {'remark': 'x'})
chk('⭐ 账实相符不可处理 BP40001', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

print()
print('  通过 %d / 失败 %d' % (ok, fail))
