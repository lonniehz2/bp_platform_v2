# -*- coding: utf-8 -*-
"""复议/异议 · 验证（合规救济通道）"""
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
PID = 870000 + int(sfx) % 100000
BIZ = 700000 + int(sfx) % 100000
print('=' * 78)
print(' 复议/异议 · 合规救济通道验证')
print('=' * 78)

# ---------- 1. 提出申诉 ----------
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'ANNUAL_REVIEW', 'bizId': BIZ, 'personId': PID, 'orgId': 1,
    'appealType': 'SUBMIT',
    'appealReason': '我家庭实际月收入 5200 元，未超过 6000 元标准，'
                    '年审认定超标系遗漏配偶失业情况，请求复核',
    'appealEvidence': 'https://x/income.pdf,https://x/unemploy.pdf',
    'daysFromNow': 10})
chk('⭐ 提出申诉（年审结论不服）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
ap = r.get('data') or {}
apId = ap.get('id')
chk('申诉单号 AP 开头', str(ap.get('appealNo', '')).startswith('AP'), ap.get('appealNo'))
chk('业务类型标签=年度核查', ap.get('bizTypeLabel') == '年度核查', ap.get('bizTypeLabel'))
chk('状态 SUBMITTED/已提交', ap.get('appealStatus') == 'SUBMITTED'
    and ap.get('appealStatusLabel') == '已提交', ap.get('appealStatus'))
chk('⭐ 申诉期限已计算（10 天）', bool(ap.get('deadlineTime')), ap.get('deadlineTime'))
chk('未超期', ap.get('overdue') in (False, 'false'), ap.get('overdue'))
chk('告知状态未告知', ap.get('notified') in (False, 'false'), ap.get('notified'))

# 同业务对象重复申诉被拒
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'ANNUAL_REVIEW', 'bizId': BIZ, 'personId': PID, 'appealType': 'SUBMIT',
    'appealReason': '再申诉一次'})
chk('⭐ 同业务对象重复申诉被拒', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 参数校验
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'BAD', 'bizId': BIZ, 'personId': PID, 'appealType': 'SUBMIT',
    'appealReason': 'x'})
chk('非法业务类型被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'PUBLICITY', 'bizId': BIZ + 1, 'personId': PID, 'appealType': 'BAD',
    'appealReason': 'x'})
chk('非法申诉类型被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'PUBLICITY', 'bizId': BIZ + 2, 'personId': PID, 'appealType': 'OBJECTION'})
chk('理由为空被拒', r.get('code') == 'BP10001', r.get('code'))

# ---------- 2. 状态机 ----------
st, r = call('POST', '/api/v1/appeals/%s/decide' % apId, {
    'decision': 'UPHELD', 'resultEffect': 'RESTORE'})
chk('⭐ 已提交不可直接决定（不可跳步）', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))
st, r = call('POST', '/api/v1/appeals/%s/investigate' % apId, {'userId': 9005})
chk('⭐ 未受理不可直接调查', r.get('code') == 'BP40001', r.get('code'))

st, r = call('POST', '/api/v1/appeals/%s/accept' % apId, {'userId': 9001})
chk('受理 → ACCEPTED/已受理', (r.get('data') or {}).get('appealStatus') == 'ACCEPTED',
    str(r.get('code')) + ' ' + str(r.get('message')))
chk('受理时间已记录', bool((r.get('data') or {}).get('acceptTime')),
    (r.get('data') or {}).get('acceptTime'))
chk('受理人已记录', str((r.get('data') or {}).get('acceptUserId')) == '9001',
    (r.get('data') or {}).get('acceptUserId'))

st, r = call('POST', '/api/v1/appeals/%s/investigate' % apId, {'userId': 9005})
chk('调查 → INVESTIGATING/调查中',
    (r.get('data') or {}).get('appealStatus') == 'INVESTIGATING', r.get('code'))

# ---------- 3. ⭐ 决定：异议成立 → 恢复资格 ----------
st, r = call('POST', '/api/v1/appeals/%s/decide' % apId, {
    'decision': 'UPHELD',
    'handleResult': '经核实，配偶已于 2026-03 失业，家庭月收入合计 5200 元，未超标',
    'reviewOpinion': '异议成立，撤销年审调租决定，恢复原租金标准',
    'resultEffect': 'RESTORE', 'handleUserId': 9003})
chk('⭐⭐ 决定：异议成立', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
dec = r.get('data') or {}
chk('⭐ 状态 UPHELD/异议成立', dec.get('appealStatus') == 'UPHELD'
    and dec.get('appealStatusLabel') == '异议成立', dec.get('appealStatus'))
chk('⭐⭐ 结果影响 RESTORE/恢复资格', dec.get('resultEffect') == 'RESTORE'
    and dec.get('resultEffectLabel') == '恢复资格',
    (dec.get('resultEffect'), dec.get('resultEffectLabel')))
chk('⭐ 标记为改变了原结论', dec.get('changesOutcome') in (True, 'true'),
    dec.get('changesOutcome'))
chk('调查核实情况已记录', '配偶已于 2026-03 失业' in str(dec.get('handleResult')),
    dec.get('handleResult'))
chk('决定时间已记录', bool(dec.get('handleTime')), dec.get('handleTime'))

# ---------- 4. 终止态保护 ----------
st, r = call('POST', '/api/v1/appeals/%s/accept' % apId, {'userId': 9001})
chk('⭐ UPHELD 终态不可再受理', r.get('code') == 'BP40001', r.get('code'))
st, r = call('POST', '/api/v1/appeals/%s/withdraw' % apId, {'reason': 'x'})
chk('⭐ 终态不可撤回', r.get('code') == 'BP40001', r.get('code'))

# ---------- 5. 告知 ----------
st, r = call('POST', '/api/v1/appeals/%s/notify' % apId, {})
chk('⭐⭐ 告知结果 → SENT', (r.get('data') or {}).get('notified') in (True, 'true'),
    (r.get('data') or {}).get('notified'))

# ---------- 6. ⭐ 异议不成立时结果影响必须为 NONE ----------
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'REVIEW', 'bizId': BIZ + 10, 'personId': PID + 1, 'appealType': 'SUBMIT',
    'appealReason': '审核不通过不合理'})
ap2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/appeals/%s/accept' % ap2, {'userId': 9001})
call('POST', '/api/v1/appeals/%s/investigate' % ap2, {'userId': 9005})
st, r = call('POST', '/api/v1/appeals/%s/decide' % ap2, {
    'decision': 'REJECTED', 'resultEffect': 'RESTORE',
    'reviewOpinion': '材料齐全，审核结论正确'})
chk('⭐⭐ 异议不成立却要恢复资格 → 拒绝（逻辑矛盾）', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拒绝信息：%s' % r.get('message'))

st, r = call('POST', '/api/v1/appeals/%s/decide' % ap2, {
    'decision': 'REJECTED', 'resultEffect': 'NONE',
    'handleResult': '经核查收入申报属实', 'reviewOpinion': '异议不成立，维持原决定'})
chk('异议不成立（NONE）→ REJECTED',
    (r.get('data') or {}).get('appealStatus') == 'REJECTED', r.get('code'))
chk('未改变原结论', (r.get('data') or {}).get('changesOutcome') in (False, 'false'),
    (r.get('data') or {}).get('changesOutcome'))

# ---------- 7. 撤回 ----------
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'PUBLICITY', 'bizId': BIZ + 20, 'personId': PID + 2,
    'appealType': 'OBJECTION', 'appealReason': '公示名单遗漏本人'})
ap3 = (r.get('data') or {}).get('id')
chk('公示异议可提出', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/appeals/%s/withdraw' % ap3, {'reason': '已线下沟通解决'})
chk('⭐ 撤回 → WITHDRAWN/已撤回',
    (r.get('data') or {}).get('appealStatus') == 'WITHDRAWN', r.get('code'))
chk('撤回原因已记录', '线下沟通' in str((r.get('data') or {}).get('reviewOpinion')),
    (r.get('data') or {}).get('reviewOpinion'))

# ---------- 8. 未办结不可告知 ----------
st, r = call('POST', '/api/v1/appeals/%s/notify' % ap3, {})
chk('⭐ 已撤回（终态）可告知', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'EXIT', 'bizId': BIZ + 30, 'personId': PID + 3, 'appealType': 'SUBMIT',
    'appealReason': '不应退出保障'})
ap4 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/appeals/%s/notify' % ap4, {})
chk('⭐ 未办结不可告知', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 9. 超期 ----------
st, r = call('POST', '/api/v1/appeals/mark-timeout', {})
chk('超期标记接口', r.get('code') == 'BP00000', r.get('code'))

# ---------- 10. 查询 ----------
st, r = call('GET', '/api/v1/appeals/by-biz?bizType=ANNUAL_REVIEW&bizId=%s' % BIZ)
chk('⭐ 按业务对象查申诉', r.get('code') == 'BP00000' and len(r.get('data') or []) >= 1,
    len(r.get('data') or []))
st, r = call('GET', '/api/v1/appeals?pageNum=1&pageSize=20&personId=%s' % PID)
chk('按人查申诉', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/appeals?pageNum=1&pageSize=20&status=UPHELD')
chk('按状态筛（异议成立）', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/appeals/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
