# -*- coding: utf-8 -*-
"""配租全链路验证：轮候 → 批次 → 摇号 → 配租 → 签约"""
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
print(' 配租全链路 · 轮候 → 批次 → 摇号 → 配租 → 签约')
print('=' * 78)

# ============ 准备：组织 + 2 个房源 ============
st, r = call('POST', '/api/v1/orgs', {'orgCode': 'AL-' + sfx, 'orgName': '配租验收小区',
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
rm1 = mkspace(fl, '101', 'ROOM', 'R1-' + sfx, '80')
rm2 = mkspace(fl, '102', 'ROOM', 'R2-' + sfx, '90')
houses = []
for i, (rid, code) in enumerate(((rm1, 'AH1-'), (rm2, 'AH2-')), start=1):
    st, r = call('POST', '/api/v1/houses', {'spaceId': int(rid), 'houseCode': code + sfx,
                                           'houseName': '10%d' % i,
                                           'houseType': 'PUBLIC_RENTAL', 'area': '80'})
    houses.append((r.get('data') or {}).get('id'))
chk('准备：2 个可配房源', all(houses), houses)

# ============ 1. 轮候入库（3 人，优先分不同）============
waitings = []
for i, (pid, appid, pri) in enumerate(((4001, 8001, '0'), (4002, 8002, '5'), (4003, 8003, '0'))):
    st, r = call('POST', '/api/v1/allocation/waiting', {
        'personId': pid, 'applicationId': appid + int(sfx), 'securityType': 'PUBLIC',
        'orgId': int(org), 'priorityScore': pri})
    chk('入轮候库（人 %d 优先分 %s）' % (pid, pri), r.get('code') == 'BP00000',
        str(r.get('code')) + ' ' + str(r.get('message')))
    waitings.append(r.get('data') or {})

w = waitings[0]
chk('轮候号 WQ 开头', str(w.get('waitingNo', '')).startswith('WQ'), w.get('waitingNo'))
chk('状态 WAITING/轮候中', w.get('queueStatus') == 'WAITING'
    and w.get('queueStatusLabel') == '轮候中', w.get('queueStatus'))

# 排名：优先分 5 的应排第 1
st, r = call('GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=20&securityType=PUBLIC&orgId=%s'
             % org)
rows = (r.get('data') or {}).get('rows') or []
mine = [x for x in rows if str(x.get('personId')) in ('4001', '4002', '4003')
        and str(x.get('orgId')) == str(org)]
chk('⭐ 轮候按排名排序', len(mine) >= 3, len(mine))
if mine:
    top = mine[0]
    print('     第1名：人 %s 总分 %s 优先分 %s 排名 %s'
          % (top.get('personId'), top.get('totalScore'), top.get('priorityScore'),
             top.get('waitingRank')))
    chk('⭐ 优先分高者排第 1', str(top.get('personId')) == '4002', top.get('personId'))
    chk('排名从 1 开始', str(top.get('waitingRank')) == '1', top.get('waitingRank'))

# 重复入队被拒
st, r = call('POST', '/api/v1/allocation/waiting', {
    'personId': 4001, 'applicationId': 8001 + int(sfx), 'securityType': 'PUBLIC'})
chk('⭐ 同申请单重复入队被拒', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 冻结/解冻
wid = w.get('id')
st, r = call('POST', '/api/v1/allocation/waiting/%s/freeze' % wid, {'reason': '材料待核'})
chk('冻结轮候', (r.get('data') or {}).get('queueStatus') == 'FROZEN', r.get('code'))
st, r = call('POST', '/api/v1/allocation/waiting/%s/unfreeze' % wid, {})
chk('解冻轮候', (r.get('data') or {}).get('queueStatus') == 'WAITING', r.get('code'))

# ============ 2. 建批次 + 房源入池 ============
st, r = call('POST', '/api/v1/allocation/batches', {
    'batchName': '2026年第一批公租房配租', 'orgId': int(org), 'securityType': 'PUBLIC',
    'batchType': 'LOTTERY', 'houseIds': [int(h) for h in houses],
    'notaryInfo': '漳州市公证处/张三/（2026）漳证字第001号'})
chk('建配租批次', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
b = r.get('data') or {}
bid = b.get('id')
chk('批次号 LB 开头', str(b.get('batchNo', '')).startswith('LB'), b.get('batchNo'))
chk('初始状态 DRAFT/草稿', b.get('batchStatus') == 'DRAFT'
    and b.get('batchStatusLabel') == '草稿', b.get('batchStatus'))
chk('⭐ 房源套数 2', str(b.get('houseCount')) == '2', b.get('houseCount'))

st, r = call('GET', '/api/v1/allocation/batches/%s/houses' % bid)
chk('批次房源池 2 套', len(r.get('data') or []) == 2, len(r.get('data') or []))

# 草稿状态不可摇号
st, r = call('POST', '/api/v1/allocation/lottery', {'batchId': int(bid)})
chk('⭐ 草稿状态不可摇号', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 发布 → 报名
st, r = call('POST', '/api/v1/allocation/batches/%s/status' % bid, {'batchStatus': 'PUBLISHED'})
chk('发布批次', (r.get('data') or {}).get('batchStatus') == 'PUBLISHED', r.get('code'))
st, r = call('POST', '/api/v1/allocation/batches/%s/status' % bid, {'batchStatus': 'SIGNUP'})
chk('进入报名', (r.get('data') or {}).get('batchStatus') == 'SIGNUP', r.get('code'))
st, r = call('POST', '/api/v1/allocation/batches/%s/status' % bid, {'batchStatus': 'CLOSED'})
chk('⭐ 状态机不可跳步（报名中→已结束被拒）', r.get('code') == 'BP40001', r.get('code'))

# ============ 3. 摇号 ============
st, r = call('POST', '/api/v1/allocation/lottery', {
    'batchId': int(bid), 'seed': 'SEED-2026-001',
    'notaryInfo': '漳州市公证处/张三/（2026）漳证字第001号'})
chk('⭐ 执行摇号', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
results = r.get('data') or []
print('     结果：%s' % [(x.get('personId'), x.get('resultTypeLabel'), x.get('selectSeq'))
                        for x in results])
chk('⭐ 摇号产生 3 条结果', len(results) == 3, len(results))
won = [x for x in results if x.get('resultType') == 'WON']
lst = [x for x in results if x.get('resultType') == 'LOST']
wl = [x for x in results if x.get('resultType') == 'WAITLIST']
chk('⭐ 中签数 = 房源数 2', len(won) == 2, len(won))
chk('⭐ 未中签 1（3人-2房源=1，无递补）', len(lst) == 1 and len(wl) == 0,
    (len(lst), len(wl)))
chk('⭐ 优先分高者（4002）中签',
    any(str(x.get('personId')) == '4002' for x in won),
    [x.get('personId') for x in won])
chk('中签者有选房序号', all(x.get('selectSeq') for x in won),
    [x.get('selectSeq') for x in won])
chk('摇号序号已留痕', all(x.get('lotterySeq') for x in results), None)

st, r = call('GET', '/api/v1/allocation/batches/%s' % bid)
bb = r.get('data') or {}
chk('批次状态 LOTTERY_DONE/摇号完成', bb.get('batchStatus') == 'LOTTERY_DONE',
    bb.get('batchStatus'))
chk('⭐ 摇号种子已落库（可复现/可公证）', bb.get('lotterySeed') == 'SEED-2026-001',
    bb.get('lotterySeed'))
chk('参与人数 3', str(bb.get('applicantCount')) == '3', bb.get('applicantCount'))

# 幂等：重复摇号被拒
st, r = call('POST', '/api/v1/allocation/lottery', {'batchId': int(bid)})
chk('⭐ 重复摇号被拒（幂等）', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# ============ 4. 配租 ============
won1 = won[0]
st, r = call('POST', '/api/v1/allocation/allocations', {
    'batchId': int(bid), 'houseId': int(houses[0]), 'personId': int(won1.get('personId')),
    'lotteryResultId': int(won1.get('id')),
    'planRentStart': '2026-12-01', 'planRentEnd': '2027-11-30'})
chk('⭐ 生成配租单', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
a1 = r.get('data') or {}
aid1 = a1.get('id')
chk('配租单号 BA 开头', str(a1.get('allocationNo', '')).startswith('BA'), a1.get('allocationNo'))
chk('状态 PENDING_SIGN/待签约', a1.get('allocationStatus') == 'PENDING_SIGN'
    and a1.get('allocationStatusLabel') == '待签约', a1.get('allocationStatus'))
chk('⭐ 已设锁定到期时间', bool(a1.get('lockExpireTime')), a1.get('lockExpireTime'))
chk('⭐ 剩余锁定小时 > 0', int(a1.get('lockRemainHours') or 0) > 0, a1.get('lockRemainHours'))
chk('未超时', a1.get('lockOverdue') in (False, 'false'), a1.get('lockOverdue'))

# 房源池状态 LOCKED
st, r = call('GET', '/api/v1/allocation/batches/%s/houses?inPoolStatus=LOCKED' % bid)
chk('⭐ 房源已锁定（LOCKED）', len(r.get('data') or []) == 1, r.get('data'))

# 同一房源不可重复配租
won2 = won[1] if len(won) > 1 else won[0]
st, r = call('POST', '/api/v1/allocation/allocations', {
    'batchId': int(bid), 'houseId': int(houses[0]), 'personId': int(won2.get('personId'))})
chk('⭐ 已锁定房源不可再配租', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 未中签者不可配租
lost = lst[0] if lst else None
if lost:
    st, r = call('POST', '/api/v1/allocation/allocations', {
        'batchId': int(bid), 'houseId': int(houses[1]),
        'personId': int(lost.get('personId')),
        'lotteryResultId': int(lost.get('id'))})
    chk('⭐ 未中签者不可配租', r.get('code') == 'BP40001',
        str(r.get('code')) + ' ' + str(r.get('message')))

# 同人不可重复持待签单
st, r = call('POST', '/api/v1/allocation/allocations', {
    'batchId': int(bid), 'houseId': int(houses[1]), 'personId': int(won1.get('personId'))})
chk('⭐ 同人已有待签单被拒', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 第二个人配租另一套
st, r = call('POST', '/api/v1/allocation/allocations', {
    'batchId': int(bid), 'houseId': int(houses[1]), 'personId': int(won2.get('personId')),
    'lotteryResultId': int(won2.get('id'))})
chk('第二人配租成功', r.get('code') == 'BP00000', r.get('code'))
aid2 = (r.get('data') or {}).get('id')

# ============ 5. 签约 ============
st, r = call('POST', '/api/v1/allocation/allocations/%s/sign' % aid1, {})
chk('⭐ 签约 → SIGNED/已签约',
    (r.get('data') or {}).get('allocationStatus') == 'SIGNED', r.get('code'))
st, r = call('GET', '/api/v1/allocation/batches/%s/houses?inPoolStatus=SELECTED' % bid)
chk('⭐ 房源池置 SELECTED/已选中', len(r.get('data') or []) == 1, r.get('data'))
st, r = call('POST', '/api/v1/allocation/allocations/%s/sign' % aid1, {})
chk('⭐ 重复签约被拒', r.get('code') == 'BP40001', r.get('code'))

# ============ 6. 放弃配租 → 房源回池 ============
st, r = call('POST', '/api/v1/allocation/allocations/%s/give-up' % aid2, {'reason': '承租人放弃'})
chk('⭐ 放弃配租 → CANCELLED',
    (r.get('data') or {}).get('allocationStatus') == 'CANCELLED', r.get('code'))
st, r = call('GET', '/api/v1/allocation/batches/%s/houses?inPoolStatus=AVAILABLE' % bid)
chk('⭐ 放弃后房源回池 AVAILABLE', len(r.get('data') or []) == 1, r.get('data'))

# ============ 7. 超时释放 ============
st, r = call('POST', '/api/v1/allocation/allocations', {
    'batchId': int(bid), 'houseId': int(houses[1]), 'personId': int(won2.get('personId')),
    'lockHours': 1})
chk('配租（锁定 1 小时）', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/allocation/allocations/release-expired', {})
chk('释放超时扫描接口', r.get('code') == 'BP00000', r.get('code'))
print('     本次释放：%s 个' % r.get('data'))
# 刚创建的未超时，不应被释放
st, r = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=20&batchId=%s' % bid)
arows = (r.get('data') or {}).get('rows') or []
pending = [x for x in arows if x.get('allocationStatus') == 'PENDING_SIGN']
chk('⭐ 未超时的待签单未被误释放', len(pending) >= 1, len(pending))

# ============ 8. 退出轮候 ============
st, r = call('POST', '/api/v1/allocation/waiting/%s/exit' % wid, {'reason': '已通过其他渠道解决'})
chk('⭐ 退出轮候 → EXITED', (r.get('data') or {}).get('queueStatus') == 'EXITED', r.get('code'))
st, r = call('POST', '/api/v1/allocation/waiting/%s/freeze' % wid, {'reason': 'x'})
chk('⭐ 已退出不可冻结', r.get('code') == 'BP40001', r.get('code'))

# ============ 9. 查询 ============
st, r = call('GET', '/api/v1/allocation/batches?pageNum=1&pageSize=20&orgId=%s' % org)
chk('批次分页', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1, (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=20&personId=4001')
chk('按人查配租单', r.get('code') == 'BP00000', r.get('code'))
st, r = call('GET', '/api/v1/allocation/waiting/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))
st, r = call('GET', '/api/v1/allocation/batches/999999999')
chk('批次不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
