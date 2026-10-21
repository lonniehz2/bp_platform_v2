# -*- coding: utf-8 -*-
"""页面完整性验证：7 个新功能的 UI 与接口是否都通"""
import json
import re
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
print('=' * 78)
print(' 页面完整性验证 · 7 个新功能')
print('=' * 78)

# ---------- 1. HTML 结构 ----------
html = urllib.request.urlopen(BASE + '/', timeout=20).read().decode('utf-8')
print('     页面大小：%.1f KB' % (len(html) / 1024))

tabs = re.findall(r'data-t="([^"]+)"', html)
chk('⭐ 页签数量 = 20', len(tabs) == 20, len(tabs))
for t in ('p-pub', 'p-review', 'p-appeal', 'p-credit'):
    chk('新页签存在 %s' % t, t in tabs, tabs)

for pid in ('p-pub', 'p-review', 'p-appeal', 'p-credit'):
    chk('面板存在 %s' % pid, 'id="%s"' % pid in html, None)

# 合同页新增 3 卡
for fn in ('addCohabitant', 'createChange', 'applyExchange'):
    chk('合同页函数存在 %s' % fn, fn in html, None)
for fn in ('createPublicity', 'pbAction', 'checkAllocPub'):
    chk('公示页函数存在 %s' % fn, fn in html, None)
for fn in ('createReview', 'finishReview', 'reviewBatch'):
    chk('年审页函数存在 %s' % fn, fn in html, None)
for fn in ('submitAppeal', 'decideAppeal', 'apNotify'):
    chk('复议页函数存在 %s' % fn, fn in html, None)
for fn in ('recordCredit', 'checkBan', 'ctAction'):
    chk('信用页函数存在 %s' % fn, fn in html, None)

# 接口清单
for kw in ('/api/v1/publicities', '/api/v1/annual-reviews', '/api/v1/appeals',
           '/api/v1/credits', '/api/v1/exchanges', '/contract-changes',
           '/cohabitants'):
    chk('接口清单含 %s' % kw, kw in html, None)

# ---------- 2. 每个页签对应的接口真实可用 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'UI-' + sfx, 'orgName': '页面验证',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')


def mkspace(parent, name, typ, code, area=None):
    b = {'orgId': int(org), 'spaceCode': code, 'spaceName': name, 'spaceType': typ}
    if parent:
        b['parentId'] = int(parent)
    if area:
        b['area'] = area
    st_, rr = call('POST', '/api/v1/spaces', b)
    return (rr.get('data') or {}).get('id')


bd = mkspace(None, '1幢', 'BUILDING', 'B-' + sfx)
un = mkspace(bd, '1单元', 'UNIT', 'U-' + sfx)
fl = mkspace(un, '1层', 'FLOOR', 'F-' + sfx)
rm = mkspace(fl, '101', 'ROOM', 'R-' + sfx, '80')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'UIH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')
PID = 920000 + int(sfx) % 100000
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': PID, 'lesseeName': '页面演示',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})

print()
print('  ── 各页签接口连通性 ──')

# 同住人
st, r = call('POST', '/api/v1/contracts/%s/cohabitants' % cid,
             {'memberName': '演示甲', 'relation': 'SPOUSE'})
chk('[合同] 同住人添加', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/contracts/%s/cohabitants/household-size' % cid)
chk('[合同] 保障人口 = 2', str(r.get('data')) == '2', r.get('data'))

# 变更
st, r = call('POST', '/api/v1/contracts/%s/changes' % cid,
             {'changeType': 'RENT_ADJUST', 'newMonthlyRent': '1200', 'changeReason': '演示调租'})
chgId = (r.get('data') or {}).get('id')
chk('[合同] 发起变更', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/contract-changes/%s/approve' % chgId, {})
chk('[合同] 变更批准（写回）', (r.get('data') or {}).get('approveStatus') == 'APPROVED',
    r.get('code'))
st, r = call('GET', '/api/v1/contracts/%s' % cid)
chk('[合同] 租金已写回 1200', str((r.get('data') or {}).get('monthlyRent')) == '1200.00',
    (r.get('data') or {}).get('monthlyRent'))

# 换房
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(fl),
                                       'spaceCode': 'R2-' + sfx, 'spaceName': '102',
                                       'spaceType': 'ROOM', 'area': '90'})
rm2 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm2), 'houseCode': 'UIH2-' + sfx,
                                       'houseName': '102', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '90'})
house2 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/exchanges', {
    'personId': PID, 'oldContractId': int(cid), 'oldHouseId': int(house),
    'newHouseId': int(house2), 'exchangeType': 'VOLUNTARY'})
chk('[合同] 换房申请', r.get('code') == 'BP00000', r.get('code'))

# 公示
d = time.strftime('%Y-%m-%d')
import datetime as dt
d6 = (dt.date.today() + dt.timedelta(days=6)).isoformat()
st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': int(org), 'title': '页面演示配租公示',
    'startDate': d, 'endDate': d6})
chk('[公示] 创建配租公示（7天）', r.get('code') == 'BP00000', r.get('code'))
pubId = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/publicities/%s/publish' % pubId, {})
chk('[公示] 发布', (r.get('data') or {}).get('publicityStatus') == 'PUBLISHED', r.get('code'))
st, r = call('GET', '/api/v1/publicities/allocation-check?orgId=%s' % org)
chk('[公示] 配租公示检查接口', r.get('code') == 'BP00000', r.get('code'))

# 年审
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': PID, 'contractId': int(cid), 'houseId': int(house),
    'reviewYear': '2026', 'reviewType': 'ANNUAL'})
rvId = (r.get('data') or {}).get('id')
chk('[年审] 创建复核单', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/annual-reviews/%s/start' % rvId, {})
chk('[年审] 开始复核', (r.get('data') or {}).get('reviewStatus') == 'REVIEWING', r.get('code'))
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rvId,
             {'reviewResult': 'KEEP'})
chk('[年审] 完成复核（KEEP）', (r.get('data') or {}).get('reviewStatus') == 'DONE', r.get('code'))

# 复议
st, r = call('POST', '/api/v1/appeals', {
    'bizType': 'ANNUAL_REVIEW', 'bizId': int(rvId), 'personId': PID,
    'appealType': 'SUBMIT', 'appealReason': '页面演示申诉'})
apId = (r.get('data') or {}).get('id')
chk('[复议] 提出申诉', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/appeals/%s/accept' % apId, {'userId': 9001})
chk('[复议] 受理', (r.get('data') or {}).get('appealStatus') == 'ACCEPTED', r.get('code'))
st, r = call('POST', '/api/v1/appeals/%s/investigate' % apId, {'userId': 9005})
chk('[复议] 调查', (r.get('data') or {}).get('appealStatus') == 'INVESTIGATING', r.get('code'))
st, r = call('POST', '/api/v1/appeals/%s/decide' % apId, {
    'decision': 'REJECTED', 'resultEffect': 'NONE', 'reviewOpinion': '异议不成立'})
chk('[复议] 作出决定', (r.get('data') or {}).get('appealStatus') == 'REJECTED', r.get('code'))

# 信用
st, r = call('POST', '/api/v1/credits', {
    'personId': PID + 1, 'violationType': 'SUBLEASE', 'sanctionType': 'BAN_APPLY',
    'violationDesc': '页面演示失信'})
chk('[信用] 记入失信', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/credits/check-ban?personId=%s' % (PID + 1))
chk('[信用] 禁申校验拦截', r.get('code') == 'BP40001', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
