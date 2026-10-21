# -*- coding: utf-8 -*-
"""信用惩戒验证：失信是否真正阻止申请"""
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
PID = 890000 + int(sfx) % 100000
print('=' * 78)
print(' 信用惩戒 · 失信是否真正阻止再申请')
print('=' * 78)

# ---------- 1. 申请前：无失信记录 ----------
st, r = call('GET', '/api/v1/credits/check-ban?personId=%s' % PID)
chk('⭐ 初始无失信 → 可正常申请', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 2. 记入失信：转租出借 → 限制申请 5 年 ----------
st, r = call('POST', '/api/v1/credits', {
    'personId': PID, 'bizType': 'CONTRACT', 'bizId': 1001,
    'violationType': 'SUBLEASE',
    'violationDesc': '将保障房转租他人牟利，经查证属实',
    'evidenceUrl': 'https://x/photo1.jpg,https://x/report.pdf',
    'sanctionType': 'BAN_APPLY',
    'decideOrgId': 1, 'decideUserId': 9003,
    'legalDocNo': '漳住保决字〔2026〕第 008 号',
    'pushToPlatform': True, 'pushPlatform': '四川住房保障管理服务平台'})
chk('⭐ 记入失信（转租出借）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
cr = r.get('data') or {}
crId = cr.get('id')
chk('记录号 CR 开头', str(cr.get('recordNo', '')).startswith('CR'), cr.get('recordNo'))
chk('违规类型标签=转租出借', cr.get('violationTypeLabel') == '转租出借',
    cr.get('violationTypeLabel'))
chk('惩戒措施标签=限制申请', cr.get('sanctionTypeLabel') == '限制申请',
    cr.get('sanctionTypeLabel'))
chk('⭐⭐ 严重违规默认限 5 年', str(cr.get('banYears')) == '5', cr.get('banYears'))
chk('⭐ 起止日已计算', bool(cr.get('banStartDate')) and bool(cr.get('banEndDate')),
    (cr.get('banStartDate'), cr.get('banEndDate')))
chk('⭐⭐ 处于限制期 underBan=true', cr.get('underBan') in (True, 'true'),
    cr.get('underBan'))
chk('状态 EFFECTIVE/生效中', cr.get('status') == 'EFFECTIVE', cr.get('status'))
chk('推送状态 PENDING/待推送', cr.get('pushStatus') == 'PENDING', cr.get('pushStatus'))
chk('法律文书号已记录', cr.get('legalDocNo') == '漳住保决字〔2026〕第 008 号',
    cr.get('legalDocNo'))
print('     限制期：%s ~ %s（%s 年）'
      % (cr.get('banStartDate'), cr.get('banEndDate'), cr.get('banYears')))

# ---------- 3. ⭐⭐ 失信后申请被真正阻止 ----------
st, r = call('GET', '/api/v1/credits/check-ban?personId=%s' % PID)
chk('⭐⭐ 失信后申请校验被拒', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拒绝信息：%s' % r.get('message'))
chk('拒绝信息含违规类型', '转租出借' in str(r.get('message')), r.get('message'))
chk('拒绝信息含解禁日期', '解禁日期' in str(r.get('message')), r.get('message'))

# 实际申请保障房也被拦（通过批次/轮候入口验证：轮候不校验，这里验证 API 层提示）
st, r = call('GET', '/api/v1/credits/by-person/%s' % PID)
chk('⭐ 按人查信用记录', r.get('code') == 'BP00000' and len(r.get('data') or []) >= 1,
    len(r.get('data') or []))

# ---------- 4. 其它惩戒类型 ----------
st, r = call('POST', '/api/v1/credits', {
    'personId': PID, 'violationType': 'ARREARS',
    'violationDesc': '恶意欠租 6 个月，催缴无果',
    'sanctionType': 'TERMINATE'})
chk('记入失信（恶意欠租→终止资格）', r.get('code') == 'BP00000', r.get('code'))
cr2 = r.get('data') or {}
chk('终止资格不计算限制年限', cr2.get('banYears') is None, cr2.get('banYears'))
chk('不推送平台（默认 NONE）', cr2.get('pushStatus') == 'NONE', cr2.get('pushStatus'))

st, r = call('POST', '/api/v1/credits', {
    'personId': PID, 'violationType': 'ILLEGAL',
    'violationDesc': '从事违法活动', 'sanctionType': 'BAN_APPLY', 'banYears': 3})
chk('⭐ 可自定义限制年限 3 年', str((r.get('data') or {}).get('banYears')) == '3',
    (r.get('data') or {}).get('banYears'))

st, r = call('POST', '/api/v1/credits', {
    'personId': PID, 'violationType': 'VACANT',
    'violationDesc': '房屋长期空置', 'sanctionType': 'CREDIT_PLATFORM'})
chk('推送信用平台类自动置 PENDING',
    (r.get('data') or {}).get('pushStatus') == 'PENDING',
    (r.get('data') or {}).get('pushStatus'))

# ---------- 5. 参数校验 ----------
st, r = call('POST', '/api/v1/credits', {
    'personId': PID, 'violationType': 'BAD', 'sanctionType': 'BAN_APPLY'})
chk('非法违规类型被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/credits', {
    'personId': PID, 'violationType': 'OTHER', 'sanctionType': 'BAD'})
chk('非法惩戒措施被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/credits', {'violationType': 'OTHER', 'sanctionType': 'FINE'})
chk('缺人员被拒', r.get('code') == 'BP10001', r.get('code'))

# ---------- 6. 推送信用平台 ----------
st, r = call('POST', '/api/v1/credits/%s/push' % crId,
             {'success': True, 'platform': '四川住房保障管理服务平台'})
chk('⭐ 标记推送成功 → PUSHED',
    (r.get('data') or {}).get('pushStatus') == 'PUSHED', r.get('code'))
chk('推送时间已记录', bool((r.get('data') or {}).get('pushTime')),
    (r.get('data') or {}).get('pushTime'))
chk('已推送标记', (r.get('data') or {}).get('pushed') in (True, 'true'),
    (r.get('data') or {}).get('pushed'))

# ---------- 7. 撤销（复议纠错）----------
st, r = call('POST', '/api/v1/credits/%s/revoke' % crId, {'reason': '复议认定转租证据不足'})
chk('⭐ 撤销信用记录 → REVOKED',
    (r.get('data') or {}).get('status') == 'REVOKED', r.get('code'))
chk('撤销原因已记录', '复议认定' in str((r.get('data') or {}).get('remark')),
    (r.get('data') or {}).get('remark'))
chk('撤销后不再处于限制期', (r.get('data') or {}).get('underBan') in (False, 'false'),
    (r.get('data') or {}).get('underBan'))
st, r = call('POST', '/api/v1/credits/%s/revoke' % crId, {'reason': 'x'})
chk('⭐ 终态不可重复撤销', r.get('code') == 'BP40001', r.get('code'))

# ---------- 8. ⭐⭐ 撤销后限制解除 ----------
# 仍有 ILLEGAL 3 年限期，故仍受限
st, r = call('GET', '/api/v1/credits/check-ban?personId=%s' % PID)
chk('⭐ 仍有其它限制记录 → 依然受限', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ---------- 9. 干净人员仍可申请 ----------
st, r = call('GET', '/api/v1/credits/check-ban?personId=%s' % (PID + 999))
chk('⭐ 无失信人员不受影响', r.get('code') == 'BP00000', r.get('code'))

# ---------- 10. 期满扫描 ----------
st, r = call('POST', '/api/v1/credits/scan-expired', {})
chk('期满扫描接口', r.get('code') == 'BP00000', r.get('code'))
print('     本次解除：%s 条' % r.get('data'))

# ---------- 11. 查询 ----------
st, r = call('GET', '/api/v1/credits?pageNum=1&pageSize=20&personId=%s' % PID)
chk('分页查询', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 4,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/credits?pageNum=1&pageSize=20&violationType=SUBLEASE')
chk('按违规类型筛', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/credits/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
