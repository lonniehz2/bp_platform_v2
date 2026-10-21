# -*- coding: utf-8 -*-
"""合同模块 · 真实接口验证"""
import json
import time
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


sfx = str(int(time.time()))[-5:]
print('=' * 72)
print(' 合同 · 真实接口验证')
print('=' * 72)


def mkc(rent='1000', subsidy='300', sign='ELECTRONIC',
        start='2026-01-01', end='2027-01-01'):
    return call('POST', '/api/v1/contracts', {
        'contractType': 'PUBLIC_RENTAL', 'orgId': 7001, 'lessorOrgId': 7100,
        'lesseePersonId': 4001, 'lesseeName': '张三', 'lesseePhone': '13800138000',
        'lesseeIdCardMask': '110105********002X',
        'houseId': 5001, 'spaceId': 6001,
        'houseAddress': '1幢1单元1层101室', 'houseArea': '89.50',
        'leaseStart': start, 'leaseEnd': end,
        'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH',
        'monthlyRent': rent, 'depositAmount': '1000', 'subsidyAmount': subsidy,
        'payCycle': 'MONTH', 'payDay': 5, 'signType': sign, 'remark': '保障房合同'})


st, r = mkc()
chk('起草合同', r.get('code') == 'BP00000', str(r.get('code')) + ' ' + str(r.get('message')))
c = r.get('data') or {}
cid = c.get('id')
chk('状态 DRAFT/草稿', c.get('contractStatus') == 'DRAFT' and c.get('contractStatusLabel') == '草稿',
    c.get('contractStatus'))
chk('单号 BC 开头', str(c.get('contractNo', '')).startswith('BC'), c.get('contractNo'))
chk('⭐ 实付 = 1000-300 = 700', str(c.get('actualPay')) == '700.00', c.get('actualPay'))
chk('⭐ 租期 12 个月（整年）', str(c.get('leaseMonths')) == '12', c.get('leaseMonths'))
chk('默认开自动授权/失效', str(c.get('autoGrant')) == '1' and str(c.get('autoExpire')) == '1',
    (c.get('autoGrant'), c.get('autoExpire')))
chk('草稿不占房', c.get('occupying') in (False, 'false'), c.get('occupying'))

st, r = mkc(rent='500', subsidy='800')
chk('⭐ 补贴超月租金被拒 BP10001', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = mkc(start='2027-01-01', end='2026-01-01')
chk('止租早于起租被拒', r.get('code') == 'BP10001', r.get('code'))

# 跳步
st, r = call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('⭐ DRAFT 直接生效被拒 BP40001', r.get('code') == 'BP40001', r.get('code'))

# 生命周期
st, r = call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
chk('提交签约 → PENDING_SIGN', (r.get('data') or {}).get('contractStatus') == 'PENDING_SIGN', r.get('code'))
st, r = call('POST', '/api/v1/contracts/%s/start-signing' % cid, {'signVendor': 'QYS'})
chk('发起签署 → SIGNING', (r.get('data') or {}).get('contractStatus') == 'SIGNING', r.get('code'))
st, r = call('POST', '/api/v1/contracts/%s/sign' % cid,
             {'signFileUrl': 'https://x/c.pdf', 'signFlowId': 'FLOW-1'})
e = r.get('data') or {}
chk('⭐ 签署生效 → EFFECTIVE', e.get('contractStatus') == 'EFFECTIVE', r.get('code'))
chk('履约中标签', e.get('contractStatusLabel') == '履约中', e.get('contractStatusLabel'))
chk('⭐ 生效后占房', e.get('occupying') in (True, 'true'), e.get('occupying'))
chk('签署时间已记录', bool(e.get('signTime')), e.get('signTime'))

st, r = call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('已生效不可重复生效', r.get('code') == 'BP40001', r.get('code'))

# 纸质合同直接从待签约生效
st, r = mkc(sign='PAPER')
pid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % pid, {})
st, r = call('POST', '/api/v1/contracts/%s/sign' % pid, {'signFileUrl': 'file://paper.pdf'})
chk('⭐ 纸质合同可从待签约直接生效', (r.get('data') or {}).get('contractStatus') == 'EFFECTIVE', r.get('code'))

# 续签
st, r = mkc(start='2026-01-01', end='2026-06-01')
rid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % rid, {})
call('POST', '/api/v1/contracts/%s/start-signing' % rid, {})
call('POST', '/api/v1/contracts/%s/sign' % rid, {})
st, r = call('POST', '/api/v1/contracts/%s/renew' % rid,
             {'newLeaseEnd': '2027-06-01', 'newMonthlyRent': '1200'})
rw = r.get('data') or {}
chk('⭐ 续签 → RENEWING', rw.get('contractStatus') == 'RENEWING', r.get('code'))
chk('续签实付 = 1200-300 = 900', str(rw.get('actualPay')) == '900.00', rw.get('actualPay'))
chk('续签后起租日 = 原止租日', rw.get('leaseStart') == '2026-06-01', rw.get('leaseStart'))
chk('续签后仍占房', rw.get('occupying') in (True, 'true'), rw.get('occupying'))

# 终止
st, r = call('POST', '/api/v1/contracts/%s/terminate' % cid, {'reason': '承租人退租'})
chk('⭐ 终止 → TERMINATED', (r.get('data') or {}).get('contractStatus') == 'TERMINATED', r.get('code'))
chk('终止原因已记录', (r.get('data') or {}).get('terminateReason') == '承租人退租',
    (r.get('data') or {}).get('terminateReason'))
chk('终止后不占房', (r.get('data') or {}).get('occupying') in (False, 'false'))
st, r = call('POST', '/api/v1/contracts/%s/terminate' % cid, {'reason': 'x'})
chk('已终止不可再终止', r.get('code') == 'BP40001', r.get('code'))

# 作废
st, r = mkc()
did = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contracts/%s/cancel' % did, {'reason': '信息有误'})
chk('草稿可作废 → CANCELLED', (r.get('data') or {}).get('contractStatus') == 'CANCELLED', r.get('code'))
st, r = call('POST', '/api/v1/contracts/%s/cancel' % rid, {'reason': 'x'})
chk('⭐ 续签中不可作废（只能终止）', r.get('code') == 'BP40001', r.get('code'))

# 即将到期
st, r = mkc(start='2025-06-01', end='2026-11-10')
nid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % nid, {})
call('POST', '/api/v1/contracts/%s/start-signing' % nid, {})
call('POST', '/api/v1/contracts/%s/sign' % nid, {})
st, r = call('GET', '/api/v1/contracts/%s' % nid)
g = r.get('data') or {}
chk('30 天内到期 → expiringSoon', g.get('expiringSoon') in (True, 'true'), g.get('daysToExpire'))
print('     剩余天数:', g.get('daysToExpire'))

# 到期扫描
st, r = mkc(start='2024-01-01', end='2025-01-01')
oid2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % oid2, {})
call('POST', '/api/v1/contracts/%s/start-signing' % oid2, {})
call('POST', '/api/v1/contracts/%s/sign' % oid2, {})
st, r = call('POST', '/api/v1/contracts/expire-due')
chk('⭐ 到期扫描接口', r.get('code') == 'BP00000' and int(r.get('data') or 0) >= 1, r.get('data'))
st, r = call('GET', '/api/v1/contracts/%s' % oid2)
chk('过期合同已置 EXPIRED', (r.get('data') or {}).get('contractStatus') == 'EXPIRED',
    (r.get('data') or {}).get('contractStatus'))

# 查询
st, r = call('GET', '/api/v1/contracts?pageNum=1&pageSize=20')
chk('合同分页', r.get('code') == 'BP00000' and int((r.get('data') or {}).get('total', 0)) >= 5,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/contracts?pageNum=1&pageSize=20&status=EFFECTIVE')
chk('按状态筛选', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/contracts?pageNum=1&pageSize=20&keyword='
             + urllib.parse.quote('张三'))
chk('中文关键词搜索', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1, r.get('code'))
st, r = call('GET', '/api/v1/contracts/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 72)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 72)
