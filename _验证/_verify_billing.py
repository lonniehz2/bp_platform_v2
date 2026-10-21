# -*- coding: utf-8 -*-
"""计费引擎 · 多业态计费能力验证"""
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


sfx = str(int(time.time()))[-5:]
print('=' * 74)
print(' 计费引擎 · 多业态计费能力验证')
print('=' * 74)


def mkItem(code, name, itemType, calcMode, price, unit):
    return call('POST', '/api/v1/fin/fee-items', {
        'itemCode': code + '-' + sfx, 'itemName': name, 'itemType': itemType,
        'calcMode': calcMode, 'unitPrice': price, 'unit': unit})


def preview(itemId, **kw):
    b = {'feeItemId': itemId}
    b.update(kw)
    return call('POST', '/api/v1/fin/calc-preview', b)


# ============ 1. 各业态收费项目创建 ============
st, r = mkItem('RENT-AREA', '公租房租金(按面积)', 'RENT', 'BY_AREA', '12.50', '元/㎡·月')
chk('创建·保障房租金（按面积）', r.get('code') == 'BP00000', r.get('code'))
iArea = (r.get('data') or {}).get('id')
chk('计费方式标签=按面积', (r.get('data') or {}).get('calcModeLabel') == '按面积',
    (r.get('data') or {}).get('calcModeLabel'))

st, r = mkItem('DORM-BED', '宿舍床位费', 'RENT', 'BY_BED', '300', '元/床·月')
chk('创建·宿舍床位费（按床位）', r.get('code') == 'BP00000', r.get('code'))
iBed = (r.get('data') or {}).get('id')

st, r = mkItem('HOTEL-NIGHT', '民宿房费', 'RENT', 'BY_NIGHT', '288', '元/套·夜')
chk('创建·民宿房费（按夜）', r.get('code') == 'BP00000', r.get('code'))
iNight = (r.get('data') or {}).get('id')

st, r = mkItem('ENERGY-METER', '园区电费', 'ENERGY', 'METER', '0.65', '元/度')
chk('创建·园区电费（按抄表）', r.get('code') == 'BP00000', r.get('code'))
iMeter = (r.get('data') or {}).get('id')

st, r = mkItem('PROP-FIXED', '物业费(固定)', 'PROPERTY', 'FIXED', '150', '元/月')
chk('创建·物业费（固定额）', r.get('code') == 'BP00000', r.get('code'))
iFixed = (r.get('data') or {}).get('id')

st, r = mkItem('RENT-AREA', '重复编码', 'RENT', 'BY_AREA', '1', '元')
chk('⭐ 项目编码重复被拒 BP30002', r.get('code') == 'BP30002', r.get('code'))

st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'BAD' + sfx, 'itemName': 'x', 'itemType': 'RENT', 'calcMode': 'BY_WHATEVER'})
chk('非法计费方式被拒', r.get('code') == 'BP10001', r.get('code'))

# ============ 2. 各业态算费 ============
st, r = preview(iArea, area='89.50')
d = r.get('data') or {}
chk('⭐ 保障房：89.5㎡ × 12.50 = 1118.75', str(d.get('finalAmount')) == '1118.75',
    d.get('finalAmount'))

st, r = preview(iBed, quantity=4)
chk('⭐ 宿舍：4 床 × 300 = 1200.00',
    str((r.get('data') or {}).get('finalAmount')) == '1200.00',
    (r.get('data') or {}).get('finalAmount'))

st, r = preview(iNight, quantity=3)
chk('⭐ 民宿：3 夜 × 288 = 864.00',
    str((r.get('data') or {}).get('finalAmount')) == '864.00',
    (r.get('data') or {}).get('finalAmount'))

st, r = preview(iMeter, meterStart='1000', meterEnd='1150')
chk('⭐ 园区：用电 150 度 × 0.65 = 97.50',
    str((r.get('data') or {}).get('finalAmount')) == '97.50',
    (r.get('data') or {}).get('finalAmount'))

st, r = preview(iFixed)
chk('物业费：固定 150.00',
    str((r.get('data') or {}).get('finalAmount')) == '150.00',
    (r.get('data') or {}).get('finalAmount'))

# 参数缺失与非法
st, r = preview(iArea)
chk('⭐ 按面积缺面积被拒', r.get('code') == 'BP10001', r.get('code') + ' ' + str(r.get('message')))
st, r = preview(iBed, quantity=0)
chk('数量为 0 被拒', r.get('code') == 'BP10001', r.get('code'))
st, r = preview(iMeter, meterStart='2000', meterEnd='1000')
chk('⭐ 本次读数小于上次被拒', r.get('code') == 'BP10001', r.get('code'))

# ============ 3. 计费规则：标准价 / 折扣 / 减免 ============
st, r = call('POST', '/api/v1/fin/billing-rules', {
    'ruleCode': 'R-STD-' + sfx, 'ruleName': '公租房标准租金', 'feeItemId': iArea,
    'houseType': 'PUBLIC_RENTAL', 'ruleType': 'STANDARD',
    'priceConfig': json.dumps({'price': 10.00}), 'priority': 10})
chk('创建标准价规则', r.get('code') == 'BP00000', r.get('code'))
rstd = (r.get('data') or {}).get('id')
chk('⭐ 租金类规则需政府审批 PENDING',
    (r.get('data') or {}).get('approveStatus') == 'PENDING',
    (r.get('data') or {}).get('approveStatus'))

st, r = preview(iArea, area='100', ruleId=rstd)
chk('⭐ 未审批规则不能计费 BP40001', r.get('code') == 'BP40001',
    r.get('code') + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/fin/billing-rules/%s/approve' % rstd, {'approveById': 9003})
chk('政府限价审批通过', (r.get('data') or {}).get('approveStatus') == 'APPROVED', r.get('code'))

st, r = preview(iArea, area='100', ruleId=rstd)
chk('⭐ 规则价覆盖项目单价：100㎡ × 10.00 = 1000.00',
    str((r.get('data') or {}).get('finalAmount')) == '1000.00',
    (r.get('data') or {}).get('finalAmount'))

# 折扣规则（非租金类无需审批）
st, r = call('POST', '/api/v1/fin/billing-rules', {
    'ruleCode': 'R-DISC-' + sfx, 'ruleName': '物业费9折', 'feeItemId': iFixed,
    'ruleType': 'DISCOUNT', 'priceConfig': json.dumps({'rate': 0.9}), 'priority': 5})
rdisc = (r.get('data') or {}).get('id')
chk('非租金规则直接 APPROVED',
    (r.get('data') or {}).get('approveStatus') == 'APPROVED',
    (r.get('data') or {}).get('approveStatus'))
st, r = preview(iFixed, ruleId=rdisc)
chk('⭐ 折扣：150 × 0.9 = 135.00',
    str((r.get('data') or {}).get('finalAmount')) == '135.00',
    (r.get('data') or {}).get('finalAmount'))

# 减免规则
st, r = call('POST', '/api/v1/fin/billing-rules', {
    'ruleCode': 'R-EXM-' + sfx, 'ruleName': '廉租全免', 'feeItemId': iArea,
    'ruleType': 'EXEMPT', 'priceConfig': '{}', 'priority': 99})
rexm = (r.get('data') or {}).get('id')
call('POST', '/api/v1/fin/billing-rules/%s/approve' % rexm, {'approveById': 9003})
st, r = preview(iArea, area='100', ruleId=rexm)
chk('⭐ 减免：全额归零 0.00',
    str((r.get('data') or {}).get('finalAmount')) == '0.00',
    (r.get('data') or {}).get('finalAmount'))

# ============ 4. 阶梯计费（园区阶梯电价） ============
st, r = call('POST', '/api/v1/fin/billing-rules', {
    'ruleCode': 'R-TIER-' + sfx, 'ruleName': '阶梯电价', 'feeItemId': iMeter,
    'ruleType': 'TIERED',
    'priceConfig': json.dumps({'tiers': [{'limit': 50, 'price': 0.50},
                                         {'limit': None, 'price': 0.80}]}),
    'priority': 20})
rtier = (r.get('data') or {}).get('id')
chk('创建阶梯规则', r.get('code') == 'BP00000', r.get('code'))

# 用量 150：前 50 度 × 0.5 = 25，后 100 度 × 0.8 = 80 → 105.00
st, r = preview(iMeter, meterStart='0', meterEnd='150', ruleId=rtier)
chk('⭐ 阶梯：50×0.5 + 100×0.8 = 105.00',
    str((r.get('data') or {}).get('finalAmount')) == '105.00',
    (r.get('data') or {}).get('finalAmount'))

# 用量 30（只在第一档）：30 × 0.5 = 15.00
st, r = preview(iMeter, meterStart='0', meterEnd='30', ruleId=rtier)
chk('⭐ 阶梯：用量 30 只落第一档 = 15.00',
    str((r.get('data') or {}).get('finalAmount')) == '15.00',
    (r.get('data') or {}).get('finalAmount'))

# ============ 5. 规则查询与筛选 ============
st, r = call('GET', '/api/v1/fin/billing-rules?feeItemId=%s' % iArea)
rules = r.get('data') or []
chk('按收费项目查规则', r.get('code') == 'BP00000' and len(rules) >= 2, len(rules))
st, r = call('GET', '/api/v1/fin/billing-rules?houseType=PUBLIC_RENTAL')
chk('按房源类型筛规则（多业态）', r.get('code') == 'BP00000'
    and len(r.get('data') or []) >= 1, len(r.get('data') or []))

st, r = call('GET', '/api/v1/fin/fee-items?calcMode=BY_NIGHT')
chk('⭐ 按计费方式筛项目（找短租类）', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1, r.get('code'))
st, r = call('GET', '/api/v1/fin/fee-items?itemType=ENERGY')
chk('按项目类型筛（能耗费）', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1, r.get('code'))

st, r = call('POST', '/api/v1/fin/fee-items/%s/status' % iNight, {'enabled': False})
chk('停用收费项目', (r.get('data') or {}).get('status') == 'DISABLED', r.get('code'))
call('POST', '/api/v1/fin/fee-items/%s/status' % iNight, {'enabled': True})

st, r = call('GET', '/api/v1/fin/fee-items/999999999')
chk('不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

print()
print('-' * 74)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 74)
