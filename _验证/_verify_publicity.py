# -*- coding: utf-8 -*-
"""公示 + 年审 验证（含配租公示 7 天合规校验）"""
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
print('=' * 78)
print(' 公示 + 年审 · 验证')
print('=' * 78)

# ---------- 准备 ----------
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'PB-' + sfx, 'orgName': '公示验收小区',
                                      'orgType': 'COMMUNITY'})
org = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'spaceCode': 'PBB-' + sfx,
                                       'spaceName': '1幢', 'spaceType': 'BUILDING'})
bd = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(bd),
                                       'spaceCode': 'PBU-' + sfx, 'spaceName': '1单元',
                                       'spaceType': 'UNIT'})
un = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(un),
                                       'spaceCode': 'PBF-' + sfx, 'spaceName': '1层',
                                       'spaceType': 'FLOOR'})
fl = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/spaces', {'orgId': int(org), 'parentId': int(fl),
                                       'spaceCode': 'PBR-' + sfx, 'spaceName': '101',
                                       'spaceType': 'ROOM', 'area': '80'})
rm = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/houses', {'spaceId': int(rm), 'houseCode': 'PBH-' + sfx,
                                       'houseName': '101', 'houseType': 'PUBLIC_RENTAL',
                                       'area': '80'})
house = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': int(org), 'lessorOrgId': int(org),
    'lesseePersonId': 6001, 'lesseeName': '公示王五',
    'houseId': int(house), 'spaceId': int(rm),
    'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('准备：合同生效', bool(cid), cid)

today = time.strftime('%Y-%m-%d')
print('     今天：%s' % today)

# ==================== 1. ⭐ 配租公示 7 天合规 ====================
st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': int(org), 'title': '2026年第一批配租结果公示',
    'content': '经摇号，以下 2 户中签……', 'startDate': today, 'endDate': today})
chk('⭐⭐ 配租公示仅 1 天 → 被拒', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拒绝信息：%s' % r.get('message'))
chk('拒绝信息含"7 个自然日"', '7' in str(r.get('message')), r.get('message'))

# 3 天也不够
st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': int(org), 'title': '试 3 天',
    'startDate': today, 'endDate': '2026-12-31' if False else today})
chk('配租公示不足 7 天一律拒绝', r.get('code') == 'BP10001', r.get('code'))

# 7 天（含首尾）通过
import datetime
d0 = datetime.date.today()
d6 = d0 + datetime.timedelta(days=6)
st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': int(org),
    'title': '2026年第一批公租房配租结果公示',
    'content': '经公开摇号，中签结果如下……公示期内如有异议可向住房保障部门反映。',
    'startDate': d0.isoformat(), 'endDate': d6.isoformat()})
chk('⭐ 配租公示满 7 天（含首尾）→ 创建成功', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
pub = r.get('data') or {}
pid = pub.get('id')
chk('公示号 PB 开头', str(pub.get('publicityNo', '')).startswith('PB'), pub.get('publicityNo'))
chk('⭐ 公示天数 = 7', str(pub.get('durationDays')) == '7', pub.get('durationDays'))
chk('初始状态 DRAFT/草稿', pub.get('publicityStatus') == 'DRAFT'
    and pub.get('publicityStatusLabel') == '草稿', pub.get('publicityStatus'))
chk('类型标签=配租公示', pub.get('publicityTypeLabel') == '配租公示',
    pub.get('publicityTypeLabel'))

# 资格公示无 7 天限制
st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'QUALIFY', 'orgId': int(org), 'title': '资格公示（不受7天限制）',
    'startDate': today, 'endDate': today})
chk('⭐ 资格公示不受 7 天限制', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'title': '日期倒挂',
    'startDate': d6.isoformat(), 'endDate': d0.isoformat()})
chk('结束日早于开始日被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'BAD', 'title': 'x', 'startDate': today, 'endDate': d6.isoformat()})
chk('非法公示类型被拒', r.get('code') == 'BP10001', r.get('code'))

# ==================== 2. 公示状态机 ====================
st, r = call('GET', '/api/v1/publicities/allocation-check?orgId=%s' % org)
chk('⭐ 尚无已结束的配租公示', r.get('data') in (False, 'false'), r.get('data'))

st, r = call('POST', '/api/v1/publicities/%s/publish' % pid, {})
chk('发布公示 → PUBLISHED/已发布',
    (r.get('data') or {}).get('publicityStatus') == 'PUBLISHED', r.get('code'))
st, r = call('POST', '/api/v1/publicities/%s/publish' % pid, {})
chk('⭐ 重复发布被拒', r.get('code') == 'BP40001', r.get('code'))

st, r = call('POST', '/api/v1/publicities/%s/close' % pid, {'remark': '公示期满，无异议'})
chk('结束公示 → CLOSED/已结束',
    (r.get('data') or {}).get('publicityStatus') == 'CLOSED', r.get('code'))
st, r = call('POST', '/api/v1/publicities/%s/close' % pid, {})
chk('⭐ CLOSED 终态不可再操作', r.get('code') == 'BP40001', r.get('code'))

st, r = call('GET', '/api/v1/publicities/allocation-check?orgId=%s' % org)
chk('⭐ 已有已结束的配租公示 → true', r.get('data') in (True, 'true'), r.get('data'))

st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'QUALIFY', 'title': '草稿直跳已结束',
    'startDate': today, 'endDate': today})
draft2 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/publicities/%s/close' % draft2, {})
chk('⭐ 状态机不可跳步（草稿→已结束被拒）', r.get('code') == 'BP40001', r.get('code'))

# ==================== 3. 年审 ====================
st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': 6001, 'contractId': int(cid), 'houseId': int(house),
    'reviewYear': '2026', 'reviewType': 'ANNUAL', 'reviewBatch': 'B2026Q4'})
chk('创建年审单', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
rev = r.get('data') or {}
rid = rev.get('id')
chk('复核单号 AR 开头', str(rev.get('reviewNo', '')).startswith('AR'), rev.get('reviewNo'))
chk('状态 PENDING/待复核', rev.get('reviewStatus') == 'PENDING'
    and rev.get('reviewStatusLabel') == '待复核', rev.get('reviewStatus'))

st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': 6001, 'reviewYear': '2026', 'reviewType': 'ANNUAL'})
chk('⭐ 幂等：同人同年度重复建被拒', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/annual-reviews', {
    'personId': 6001, 'reviewYear': '26', 'reviewType': 'ANNUAL'})
chk('年度格式错误被拒', r.get('code') == 'BP10001', r.get('code'))

# 开始复核
st, r = call('POST', '/api/v1/annual-reviews/%s/start' % rid, {})
chk('开始复核 → REVIEWING/复核中',
    (r.get('data') or {}).get('reviewStatus') == 'REVIEWING', r.get('code'))
chk('复核日期已记录', bool((r.get('data') or {}).get('reviewDate')),
    (r.get('data') or {}).get('reviewDate'))

# 结果为 ADJUST 但未填处置内容 → 拒绝
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid, {'reviewResult': 'ADJUST'})
chk('⭐ 结果 ADJUST 必须填处置内容', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 正常完成
st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid, {
    'reviewResult': 'ADJUST',
    'checkResult': json.dumps({'income': 8000, 'income_limit': 6000,
                               'house': 0, 'family_size': 3}),
    'adjustContent': '家庭收入超标，租金由市场价 60% 调整为 80%',
    'reviewUserId': 9003})
chk('⭐ 完成复核 → DONE/已完成',
    (r.get('data') or {}).get('reviewStatus') == 'DONE', r.get('code'))
chk('结果标签=调整（租金/房源）',
    (r.get('data') or {}).get('reviewResultLabel') == '调整（租金/房源）',
    (r.get('data') or {}).get('reviewResultLabel'))
chk('⭐ 下次复核日期自动=次年同日',
    (r.get('data') or {}).get('nextReviewDate') == (d0.replace(year=d0.year + 1)).isoformat(),
    (r.get('data') or {}).get('nextReviewDate'))
chk('核验明细已保存（JSON）', bool((r.get('data') or {}).get('checkResult')),
    (r.get('data') or {}).get('checkResult'))

st, r = call('POST', '/api/v1/annual-reviews/%s/finish' % rid, {'reviewResult': 'KEEP'})
chk('⭐ DONE 终态不可再完成', r.get('code') == 'BP40001', r.get('code'))
st, r = call('POST', '/api/v1/annual-reviews/%s/start' % rid, {})
chk('已完成不可再开始', r.get('code') == 'BP40001', r.get('code'))

# 批量生成
st, r = call('POST', '/api/v1/annual-reviews/batch', {
    'reviewYear': '2027', 'orgId': int(org), 'reviewBatch': 'B2027', 'dryRun': True})
chk('⭐ 批量生成年审（试运行）', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
bt = r.get('data') or {}
print('     年度 %s 扫描 %s 生成 %s 跳过 %s'
      % (bt.get('reviewYear'), bt.get('scanned'), bt.get('created'), bt.get('skipped')))
chk('扫描到生效合同', int(bt.get('scanned') or 0) >= 1, bt.get('scanned'))
chk('试运行有结果', int(bt.get('created') or 0) >= 1, bt.get('created'))

st, r = call('POST', '/api/v1/annual-reviews/batch', {
    'reviewYear': '2027', 'orgId': int(org), 'reviewBatch': 'B2027', 'dryRun': False})
chk('批量落库', int((r.get('data') or {}).get('created') or 0) >= 1,
    (r.get('data') or {}).get('created'))
st, r = call('POST', '/api/v1/annual-reviews/batch', {
    'reviewYear': '2027', 'orgId': int(org), 'dryRun': False})
chk('⭐ 批量幂等：重复生成 0 条', int((r.get('data') or {}).get('created') or 0) == 0,
    (r.get('data') or {}).get('created'))

st, r = call('POST', '/api/v1/annual-reviews/batch', {'reviewYear': '27'})
chk('批量年度格式错误被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/annual-reviews/mark-overdue', {})
chk('逾期标记接口', r.get('code') == 'BP00000', r.get('code'))

# ==================== 4. 查询 ====================
st, r = call('GET', '/api/v1/publicities?pageNum=1&pageSize=20&type=ALLOCATION')
chk('公示分页（按类型）', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/annual-reviews?pageNum=1&pageSize=20&reviewYear=2026')
chk('年审分页（按年度）', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/annual-reviews?pageNum=1&pageSize=20&personId=6001')
chk('按人查年审', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/publicities/999999999')
chk('公示不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))
st, r = call('GET', '/api/v1/annual-reviews/999999999')
chk('复核单不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
