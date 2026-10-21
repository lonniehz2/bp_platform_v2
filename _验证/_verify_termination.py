# -*- coding: utf-8 -*-
"""退租腾退 · 真实接口验证"""
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


print('=' * 72)
print(' 退租腾退 · 真实接口验证')
print('=' * 72)


def mk(type_, reloc=None):
    b = {'contractId': 2001, 'houseId': 5001, 'personId': 4001,
         'terminationType': type_, 'planExitDate': '2026-11-30',
         'exitReason': '承租人工作调动'}
    if reloc is not None:
        b['relocationMonths'] = reloc
    return call('POST', '/api/v1/terminations', b)


# 1. 正常退租
st, r = mk('NORMAL')
chk('申请退租', r.get('code') == 'BP00000', str(r.get('code')) + ' ' + str(r.get('message')))
t = r.get('data') or {}
tid = t.get('id')
chk('状态 APPLYING/申请中', t.get('terminationStatus') == 'APPLYING'
    and t.get('terminationStatusLabel') == '申请中', t.get('terminationStatus'))
chk('单号 BT 开头', str(t.get('terminationNo', '')).startswith('BT'), t.get('terminationNo'))
chk('⭐ 重庆过渡期 3 个月', str(t.get('transitionMonths')) == '3', t.get('transitionMonths'))
chk('⭐ 过渡期租金倍率 1.5', str(t.get('transitionRentMultiplier')) == '1.5',
    t.get('transitionRentMultiplier'))
chk('过渡期起止日已生成', bool(t.get('transitionStartDate')) and bool(t.get('transitionEndDate')),
    (t.get('transitionStartDate'), t.get('transitionEndDate')))
chk('初始验房/结算为 PENDING', t.get('inspectStatus') == 'PENDING'
    and t.get('settleStatus') == 'PENDING', (t.get('inspectStatus'), t.get('settleStatus')))
chk('初始未释放/未回收', t.get('houseReleased') in (False, 'false')
    and t.get('grantRevoked') in (False, 'false'))
chk('初始不可办结', t.get('readyToComplete') in (False, 'false'), t.get('readyToComplete'))

# 2. 违规清退 + 成都搬迁期
st, r = mk('EXPEL')
ex = r.get('data') or {}
chk('⭐ 违规清退登记 5 年禁申', bool(ex.get('banReapplyEndDate')), ex.get('banReapplyEndDate'))

st, r = mk('EXCHANGE', 6)
rel = r.get('data') or {}
chk('⭐ 成都搬迁期 6 个月生效', bool(rel.get('relocationStartDate'))
    and bool(rel.get('relocationEndDate')), (rel.get('relocationStartDate'),
                                              rel.get('relocationEndDate')))

st, r = mk('NORMAL', 7)
chk('⭐ 搬迁期超 6 个月被拒 BP10001', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = mk('BAD')
chk('非法退租类型被拒', r.get('code') == 'BP10001', r.get('code'))

# 3. 状态机跳步
st, r = call('POST', '/api/v1/terminations/%s/approve' % tid, {'reason': 'x'})
chk('⭐ APPLYING 直接批准被拒 BP40001', r.get('code') == 'BP40001', r.get('code'))
st, r = call('POST', '/api/v1/terminations/%s/complete' % tid, {})
chk('⭐ APPLYING 直接办结被拒 BP40001', r.get('code') == 'BP40001', r.get('code'))

# 4. 审批流转
st, r = call('POST', '/api/v1/terminations/%s/submit' % tid, {})
chk('提交审批 → APPROVING', (r.get('data') or {}).get('terminationStatus') == 'APPROVING', r.get('code'))
st, r = call('POST', '/api/v1/terminations/%s/approve' % tid, {'reason': '同意退租'})
chk('批准 → APPROVED', (r.get('data') or {}).get('terminationStatus') == 'APPROVED', r.get('code'))
chk('已批准标签', (r.get('data') or {}).get('terminationStatusLabel') == '已批准',
    (r.get('data') or {}).get('terminationStatusLabel'))

# 5. 办结四前置
st, r = call('POST', '/api/v1/terminations/%s/complete' % tid, {})
chk('⭐ 验房未通过不可办结', r.get('code') == 'BP40001'
    and '验房' in str(r.get('message')), str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/terminations/%s/inspect' % tid,
             {'inspectStatus': 'ABNORMAL', 'inspectResult': '墙面有破损',
              'damageAmount': '300', 'inspectImages': 'img1.jpg'})
chk('验房记录（有异常+赔偿300）', (r.get('data') or {}).get('inspectStatus') == 'ABNORMAL'
    and str((r.get('data') or {}).get('damageAmount')) == '300.00',
    (r.get('data') or {}).get('inspectStatus'))
st, r = call('POST', '/api/v1/terminations/%s/complete' % tid, {})
chk('⭐ 验房异常仍不可办结', r.get('code') == 'BP40001', r.get('code'))

st, r = call('POST', '/api/v1/terminations/%s/inspect' % tid,
             {'inspectStatus': 'PASSED', 'inspectResult': '验收合格', 'damageAmount': '0'})
chk('重新验房通过', (r.get('data') or {}).get('inspectStatus') == 'PASSED', r.get('code'))

st, r = call('POST', '/api/v1/terminations/%s/complete' % tid, {})
chk('⭐ 结算未完成不可办结', r.get('code') == 'BP40001'
    and '结算' in str(r.get('message')), str(r.get('message')))

# 6. 结算公式
st, r = call('POST', '/api/v1/terminations/%s/settle' % tid,
             {'depositRefund': '2000', 'arrearsAmount': '500'})
s = r.get('data') or {}
chk('结算完成', s.get('settleStatus') == 'SETTLED', r.get('code'))
chk('⭐ 结算 = 2000 - 500 - 0 = 1500.00', str(s.get('settleAmount')) == '1500.00',
    s.get('settleAmount'))

st, r = call('POST', '/api/v1/terminations/%s/complete' % tid, {})
chk('⭐ 房源未释放不可办结', r.get('code') == 'BP40001'
    and '房源' in str(r.get('message')), str(r.get('message')))

st, r = call('POST', '/api/v1/terminations/%s/mark-released' % tid,
             {'houseReleased': True, 'grantRevoked': False})
st, r = call('POST', '/api/v1/terminations/%s/complete' % tid, {})
chk('⭐ 授权未回收不可办结', r.get('code') == 'BP40001'
    and '授权' in str(r.get('message')), str(r.get('message')))

st, r = call('POST', '/api/v1/terminations/%s/mark-released' % tid,
             {'houseReleased': True, 'grantRevoked': True})
chk('标记房源已释放+授权已回收', (r.get('data') or {}).get('houseReleased') in (True, 'true')
    and (r.get('data') or {}).get('grantRevoked') in (True, 'true'), r.get('code'))
st, r = call('GET', '/api/v1/terminations/%s' % tid)
chk('⭐ 四前置齐备 → readyToComplete', (r.get('data') or {}).get('readyToComplete') in (True, 'true'),
    r.get('data'))

st, r = call('POST', '/api/v1/terminations/%s/complete' % tid, {'actualExitDate': '2026-11-28'})
cp = r.get('data') or {}
chk('⭐ 办结 → COMPLETED', cp.get('terminationStatus') == 'COMPLETED', r.get('code'))
chk('办结标签=已完成', cp.get('terminationStatusLabel') == '已完成', cp.get('terminationStatusLabel'))
chk('实际退房日已记录', cp.get('actualExitDate') == '2026-11-28', cp.get('actualExitDate'))
st, r = call('POST', '/api/v1/terminations/%s/complete' % tid, {})
chk('已办结不可重复办结', r.get('code') == 'BP40001', r.get('code'))

# 7. 驳回与撤单
st, r = mk('NORMAL')
tid2 = (r.get('data') or {}).get('id')
call('POST', '/api/v1/terminations/%s/submit' % tid2, {})
st, r = call('POST', '/api/v1/terminations/%s/reject' % tid2, {'reason': '材料不全'})
chk('驳回 → REJECTED', (r.get('data') or {}).get('terminationStatus') == 'REJECTED', r.get('code'))
st, r = call('POST', '/api/v1/terminations/%s/submit' % tid2, {})
chk('⭐ REJECTED 终态不可再流转', r.get('code') == 'BP40001', r.get('code'))

st, r = mk('NORMAL')
tid3 = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/terminations/%s/cancel' % tid3, {'reason': '继续租住'})
chk('撤单 → CANCELLED', (r.get('data') or {}).get('terminationStatus') == 'CANCELLED', r.get('code'))

# 8. 强制执行登记
st, r = call('POST', '/api/v1/terminations/%s/register-enforce' % tid2,
             {'enforceApplyDate': '2026-10-19', 'enforceCourt': '芗城区人民法院',
              'itemHandlerName': '李四', 'itemHandlerPhone': '13700137000',
              'notaryNo': '公证字2026-001'})
en = r.get('data') or {}
chk('登记强制执行', en.get('enforceFlag') in (True, 'true'), r.get('code'))
chk('登记法院', en.get('enforceCourt') == '芗城区人民法院', en.get('enforceCourt'))
chk('登记物品处置人（成都）', en.get('itemHandlerName') == '李四', en.get('itemHandlerName'))
chk('登记公证', en.get('notaryFlag') in (True, 'true') and en.get('notaryNo') == '公证字2026-001',
    en.get('notaryNo'))

# 9. 逾期判定
st, r = call('POST', '/api/v1/terminations', {'contractId': 2002, 'houseId': 5002,
                                              'terminationType': 'NORMAL',
                                              'planExitDate': '2026-01-01'})
ov = (r.get('data') or {}).get('id')
st, r = call('GET', '/api/v1/terminations/%s' % ov)
chk('⭐ 逾期未退房 → overdueExit', (r.get('data') or {}).get('overdueExit') in (True, 'true'),
    (r.get('data') or {}).get('overdueExit'))

# 10. 查询与校验
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=20')
chk('退租分页', r.get('code') == 'BP00000' and int((r.get('data') or {}).get('total', 0)) >= 4,
    (r.get('data') or {}).get('total'))
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=20&status=COMPLETED')
chk('按状态筛选', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1, r.get('code'))
st, r = call('GET', '/api/v1/terminations?pageNum=1&pageSize=20&type=EXPEL')
chk('按类型筛选', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1, r.get('code'))
st, r = call('GET', '/api/v1/terminations/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 72)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 72)
