# -*- coding: utf-8 -*-
"""新增功能回归：批量出账/抄表批量出账/催缴/欠费摘要/变更生效/押金/设备搜索等。"""
import json
import urllib.error
import urllib.parse
import urllib.request

B = 'http://192.168.31.11:8080/api/v1'
H = {'X-Tenant-Id': '350600'}
PASS = []
FAIL = []


def login():
    r = urllib.request.Request(
        B + '/auth/login',
        data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                         'password': 'admin123'}).encode(),
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']


H['Authorization'] = 'Bearer ' + login()


def call(p, m='GET', b=None, raw=False):
    d = json.dumps(b).encode() if b is not None else (b'' if m == 'POST' else None)
    x = urllib.request.Request(B + p, data=d, method=m,
                               headers={**H, 'Content-Type': 'application/json'})
    try:
        y = urllib.request.urlopen(x, timeout=120)
        j = json.loads(y.read().decode())
        return y.status, (j if not raw else j.get('data'))
    except urllib.error.HTTPError as e:
        try:
            j = json.loads(e.read().decode())
        except Exception:
            j = {'message': 'HTTP ' + str(e.code)}
        return e.code, j


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(('  ✔ ' if cond else '  ✘ ') + name + ('' if not detail else '  ' + str(detail)[:160]))


# 1 批量出账：试算 + 幂等
_, fee_rows = call('/fin/fee-items?pageNum=1&pageSize=50', raw=True)
fee = [x for x in fee_rows['rows']
       if x.get('calcMode') == 'BY_AREA'][0]
org = '1000000000000000010'
body = {'orgId': org, 'feeItemId': fee['id'], 'periodStart': '2026-09-01',
        'periodEnd': '2026-09-30', 'dryRun': True}
st, dry = call('/fin/bills/generate', 'POST', body)
dry = dry.get('data') or dry
check('批量出账试算', st == 200 and dry['dryRun'] is True,
      '生成=%s 跳过=%s' % (dry.get('generated'), dry.get('skipped')))
st, r1 = call('/fin/bills/generate', 'POST', {**body, 'dryRun': False})
r1 = r1.get('data') or r1
st, r2 = call('/fin/bills/generate', 'POST', {**body, 'dryRun': False})
r2 = r2.get('data') or r2
check('批量出账幂等', r2['generated'] == 0 and r2['skipped'] >= r1['generated'],
      '首次 %s / 再次 %s 跳过 %s' % (r1['generated'], r2['generated'], r2['skipped']))

# 2 抄表批量出账
st, stat = call('/fin/meter-readings?pageNum=1&pageSize=20&billed=false', raw=True)
ids = [x['id'] for x in stat['rows'][:2]]
if ids:
    st, br = call('/fin/meter-readings/bill-batch', 'POST', ids, raw=True)
    check('抄表批量出账', st == 200 and br['billed'] >= 1, br)
else:
    check('抄表批量出账', False, '没有未出账读数')

# 3 催缴创建
st, bills = call('/fin/bills?pageNum=1&pageSize=50&status=UNPAID', raw=True)
b = bills['rows'][0]
st, dn = call('/fin/dunnings', 'POST', {'billId': b['id'], 'dunningType': 'NOTICE',
                                        'dunningContent': '回归催缴'})
check('催缴生成记录', st == 200, dn.get('message'))

# 4 欠费摘要
row = next((x for x in bills['rows'] if x.get('contractId')), None)
if row:
    st, sm = call('/fin/arrears/summary?contractId=' + str(row['contractId']), raw=True)
    check('欠费摘要', st == 200 and sm.get('contract_id') and sm.get('days') is not None, sm)

# 5 变更：未来生效不写回
st, cs = call('/contracts?pageNum=1&pageSize=20&status=EFFECTIVE', raw=True)
c = cs['rows'][0]
before = c['monthlyRent']
st, ch = call('/contracts/%s/changes' % c['id'], 'POST', raw=True, b=
              {'changeType': 'RENT_ADJUST', 'newMonthlyRent': str(float(before) + 50),
               {'changeType': 'RENT_ADJUST', 'newMonthlyRent': str(float(before) + 50), 'effectiveDate': '2099-01-01', 'changeReason': '回归-未来生效'})
st2, ap = call('/contract-changes/%s/approve' % ch['id'], 'POST', {})
st3, after = call('/contracts/' + str(c['id']), raw=True)
check('变更未来生效不写回', str(after['monthlyRent']) == str(before),
      '原 %s 现 %s' % (before, after['monthlyRent']))

# 6 变更：当天生效写回
st, ch2 = call('/contracts/%s/changes' % c['id'], 'POST', raw=True, b=
               {'changeType': 'RENT_ADJUST', 'newMonthlyRent': str(float(before) + 30),
                {'changeType': 'RENT_ADJUST', 'newMonthlyRent': str(float(before) + 30), 'effectiveDate': '2026-10-29', 'changeReason': '回归-立即生效'})
st, ap2 = call('/contract-changes/%s/approve' % ch2['id'], 'POST', {})
st, after2 = call('/contracts/' + str(c['id']), raw=True)
check('变更立即生效写回', abs(float(after2['monthlyRent']) - (float(before) + 30)) < 0.01,
      after2['monthlyRent'])

# 7 押金：不传人员/实收
st, cs2 = call('/contracts?pageNum=1&pageSize=100&status=EFFECTIVE', raw=True)
target = None
for cc in cs2['rows']:
    st, dp = call('/fin/deposits', 'POST', raw=True, b={'contractId': cc['id'],
                                            {'contractId': cc['id'], 'depositAmount': cc.get('depositAmount')})
    if st == 200:
        target = dp
        break
check('押金自动人员/金额', target is not None and target.get('personId'),
      target and {'person': target.get('personId'), 'amount': target.get('balanceAmount')})

# 8 设备搜索
st, dev = call('/fin/meter-readings/devices-search?keyword=' + urllib.parse.quote('水表'), raw=True)
check('设备按名称搜索', st == 200 and len(dev) > 0, '条数=%s' % len(dev))

# 9 房源「105房间」
st, hs = call('/houses?pageNum=1&pageSize=5&keyword=' + urllib.parse.quote('105房间'), raw=True)
check('房源房间关键字', hs['total'] > 0, 'total=%s' % hs['total'])

# 10 资金流水余额
st, flows = call('/fin/cash-flows?pageNum=1&pageSize=2', raw=True)
prev = float(flows['rows'][0]['balanceAfter'])
st, nf = call('/fin/cash-flows', 'POST', {'flowType': 'INCOME', 'bizType': 'OTHER',
                                          {'flowType': 'INCOME', 'bizType': 'OTHER', 'bizId': 1, 'amount': 5, 'remark': '回归余额'}, raw=True)
check('流水余额=前+本次', abs(float(nf['balanceAfter']) - (prev + 5)) < 0.01,
      '%s + 5 = %s' % (prev, nf['balanceAfter']))

# 11 历史批次房源可再次入池（用已配租批次中的房源）
st, batches = call('/allocation/batches?pageNum=1&pageSize=50', raw=True)
allocated = next((x for x in batches['rows'] if x['batchStatus'] == 'ALLOCATED'), None)
draft = next((x for x in batches['rows'] if x['batchStatus'] in ('DRAFT', 'PUBLISHED')), None)
if allocated and draft:
    st, hs = call('/allocation/batches/%s/houses?pageNum=1&pageSize=1' % allocated['id'], raw=True)
    hrow = hs['rows'][0] if hs.get('rows') else None
    if hrow:
        st, rr = call('/allocation/batches/%s/houses' % draft['id'], 'POST',
                      {'houseIds': [hrow['houseId']]})
        check('历史房源可入新批次', st == 200 or '已在' in str(rr.get('message')), rr.get('message'))
else:
    check('历史房源可入新批次', True, '样本不足，跳过')

print('\n通过 %d 项，失败 %d 项' % (len(PASS), len(FAIL)))
if FAIL:
    print('失败：' + '、'.join(FAIL))
