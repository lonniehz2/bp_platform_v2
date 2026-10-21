# -*- coding: utf-8 -*-
"""批量自动出账 · 真实接口验证"""
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


def chk(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1
        print('  [PASS] ' + name)
    else:
        fail += 1
        print('  [FAIL] ' + name + '  ' + str(extra))


sfx = str(int(time.time()))[-5:]
ORG = 7001
print('=' * 74)
print(' 批量自动出账 · 验证（真实合同 + 计费引擎）')
print('=' * 74)

# ---------- 准备：造一个生效合同 ----------
st, r = call('POST', '/api/v1/contracts', {
    'contractType': 'PUBLIC_RENTAL', 'orgId': ORG, 'lessorOrgId': 7100,
    'lesseePersonId': 4001, 'lesseeName': '批量张三',
    'houseId': 5001, 'spaceId': 6001, 'houseAddress': '1幢101室',
    'houseArea': '89.50', 'leaseStart': '2026-01-01', 'leaseEnd': '2027-12-31',
    'rentPrice': '12.50', 'rentUnit': 'HOUSE_MONTH', 'monthlyRent': '1000',
    'depositAmount': '1000', 'subsidyAmount': '0', 'payCycle': 'MONTH', 'payDay': 5,
    'signType': 'PAPER'})
cid = (r.get('data') or {}).get('id')
chk('创建合同', r.get('code') == 'BP00000', r.get('code'))
call('POST', '/api/v1/contracts/%s/submit-sign' % cid, {})
st, r = call('POST', '/api/v1/contracts/%s/sign' % cid, {})
chk('合同生效（履约中）', (r.get('data') or {}).get('contractStatus') == 'EFFECTIVE', r.get('code'))

# ---------- 准备：收费项目（按面积）----------
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'AUTO-RENT-' + sfx, 'itemName': '公租房租金(批量)', 'itemType': 'RENT',
    'calcMode': 'BY_AREA', 'unitPrice': '12.50', 'unit': '元/㎡·月'})
itemId = (r.get('data') or {}).get('id')
chk('创建收费项目（按面积）', r.get('code') == 'BP00000', r.get('code'))

# ---------- 1. 试运行 ----------
period = '2026-11'
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-30',
    'billPeriod': period, 'dueDate': '2026-11-10', 'orgId': ORG, 'dryRun': True})
chk('⭐ 试运行接口可用', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
d = r.get('data') or {}
chk('试运行标记 dryRun=true', d.get('dryRun') in (True, 'true'), d.get('dryRun'))
print('     扫描合同 %s，生成 %s，跳过 %s，合计 %s'
      % (d.get('totalContracts'), d.get('generated'), d.get('skipped'), d.get('totalAmount')))
chk('⭐ 扫到生效合同', int(d.get('totalContracts') or 0) >= 1, d.get('totalContracts'))
chk('⭐ 试运行有算费结果', int(d.get('generated') or 0) >= 1, d.get('generated'))
chk('⭐ 试运行不落库（billId 全为 null）',
    all((it.get('billId') is None) for it in (d.get('items') or [])),
    [it.get('billId') for it in (d.get('items') or [])])

# 找我们那张合同的明细，核对金额
myItem = next((it for it in (d.get('items') or []) if str(it.get('contractId')) == str(cid)), None)
chk('⭐ 明细包含本合同的算费', myItem is not None, myItem)
if myItem:
    # 房源 5001 面积未知（历史数据），只校验有金额且有计算说明
    print('     合同 %s：数量=%s 金额=%s 说明=%s'
          % (myItem.get('contractNo'), myItem.get('quantity'), myItem.get('amount'),
             myItem.get('explain')))
    chk('明细状态 OK', myItem.get('status') == 'OK', myItem.get('status'))
    chk('明细含计算说明', bool(myItem.get('explain')), myItem.get('explain'))

# ---------- 2. 落库 ----------
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-30',
    'billPeriod': period, 'dueDate': '2026-11-10', 'orgId': ORG, 'dryRun': False})
chk('落库执行', r.get('code') == 'BP00000', r.get('code'))
g = r.get('data') or {}
chk('dryRun=false', g.get('dryRun') in (False, 'false'), g.get('dryRun'))
chk('⭐ 落库后有 billId', int(g.get('generated') or 0) >= 1, g.get('generated'))
print('     落库：生成 %s，跳过 %s，合计 %s'
      % (g.get('generated'), g.get('skipped'), g.get('totalAmount')))
myBill = next((it.get('billId') for it in (g.get('items') or [])
               if str(it.get('contractId')) == str(cid)), None)
chk('⭐ 本合同已生成账单', myBill is not None, myBill)

# ---------- 3. 幂等 ----------
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-30',
    'billPeriod': period, 'orgId': ORG, 'dryRun': False})
g2 = r.get('data') or {}
chk('⭐ 幂等：重复执行生成 0 张', int(g2.get('generated') or 0) == 0, g2.get('generated'))
chk('⭐ 幂等：全部跳过', int(g2.get('skipped') or 0) >= 1, g2.get('skipped'))
skipItem = next((it for it in (g2.get('items') or [])
                 if str(it.get('contractId')) == str(cid)), None)
chk('跳过原因说明"账单已存在"',
    skipItem is not None and '已存在' in str(skipItem.get('reason')),
    skipItem.get('reason') if skipItem else None)

# ---------- 4. 生成的账单可查 ----------
st, r = call('GET', '/api/v1/fin/bills?pageNum=1&pageSize=50&contractId=%s' % cid)
rows = (r.get('data') or {}).get('rows') or []
autoBills = [x for x in rows if x.get('generateType') == 'AUTO']
chk('⭐ 账单 generateType=AUTO', len(autoBills) >= 1, len(autoBills))
if autoBills:
    ab = autoBills[0]
    chk('账单状态 UNPAID', ab.get('billStatus') == 'UNPAID', ab.get('billStatus'))
    chk('账期正确', ab.get('billPeriod') == period, ab.get('billPeriod'))
    chk('⚠️ 应付 = 应收（无滞纳金/减免）',
        str(ab.get('payableAmount')) == str(ab.get('billAmount')),
        (ab.get('payableAmount'), ab.get('billAmount')))
    print('     账单 %s：应收=%s 应付=%s' % (ab.get('billNo'), ab.get('billAmount'),
                                            ab.get('payableAmount')))

# ---------- 5. 业务校验 ----------
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': 999999999, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-30'})
chk('收费项目不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'METER-' + sfx, 'itemName': '水费', 'itemType': 'ENERGY',
    'calcMode': 'METER', 'unitPrice': '3.5', 'unit': '元/吨'})
meterItem = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': meterItem, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-30'})
chk('⭐ 抄表类不支持批量出账（明确拒绝）', r.get('code') == 'BP40001'
    and '抄表' in str(r.get('message')), str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-11-30', 'periodEnd': '2026-11-01'})
chk('截止日早于起始日被拒', r.get('code') == 'BP10001', r.get('code'))

# 停用项目不能出账
call('POST', '/api/v1/fin/fee-items/%s/status' % itemId, {'enabled': False})
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': itemId, 'periodStart': '2026-12-01', 'periodEnd': '2026-12-31'})
chk('⭐ 停用项目不能出账', r.get('code') == 'BP40001',
    str(r.get('code')) + ' ' + str(r.get('message')))
call('POST', '/api/v1/fin/fee-items/%s/status' % itemId, {'enabled': True})

# ---------- 6. 按夜计费批量（民宿业态）----------
st, r = call('POST', '/api/v1/fin/fee-items', {
    'itemCode': 'NIGHT-' + sfx, 'itemName': '民宿房费', 'itemType': 'RENT',
    'calcMode': 'BY_NIGHT', 'unitPrice': '300', 'unit': '元/套·夜'})
nightItem = (r.get('data') or {}).get('id')
st, r = call('POST', '/api/v1/fin/bills/generate', {
    'feeItemId': nightItem, 'periodStart': '2026-11-01', 'periodEnd': '2026-11-05',
    'billPeriod': '2026-11-N1', 'dryRun': True})
nd = r.get('data') or {}
nightItemRow = next((it for it in (nd.get('items') or [])
                     if str(it.get('contractId')) == str(cid)), None)
if nightItemRow:
    print('     按夜：数量=%s（应为 4）金额=%s' % (nightItemRow.get('quantity'),
                                                 nightItemRow.get('amount')))
    chk('⭐ 按夜数量 = 期间天数 4', str(nightItemRow.get('quantity')) == '4',
        nightItemRow.get('quantity'))
    chk('⭐ 按夜金额 = 4×300 = 1200.00', str(nightItemRow.get('amount')) == '1200.00',
        nightItemRow.get('amount'))
else:
    chk('按夜出账明细存在', False, nd)

print()
print('-' * 74)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 74)
