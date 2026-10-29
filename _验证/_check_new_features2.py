# -*- coding: utf-8 -*-
"""新增功能回归：批量出账/抄表批量出账/催缴/欠费摘要/变更生效/押金/设备搜索等。"""
import json
import urllib.error
import urllib.parse
import urllib.request

B = 'http://192.168.31.11:8080/api/v1'
H = {'X-Tenant-Id': '350600'}
PASS, FAIL = [], []


def login():
    r = urllib.request.Request(
        B + '/auth/login',
        data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                         'password': 'admin123'}).encode(),
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']


H['Authorization'] = 'Bearer ' + login()


def req(p, m='GET', body=None):
    d = json.dumps(body).encode() if body is not None else (b'' if m == 'POST' else None)
    x = urllib.request.Request(B + p, data=d, method=m,
                               headers={**H, 'Content-Type': 'application/json'})
    try:
        y = urllib.request.urlopen(x, timeout=180)
        j = json.loads(y.read().decode())
        return y.status, j.get('data'), j
    except urllib.error.HTTPError as e:
        try:
            j = json.loads(e.read().decode())
        except Exception:
            j = {'message': 'HTTP ' + str(e.code)}
        return e.code, None, j


def ok(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print(('  OK  ' if cond else '  FAIL ') + name + ('' if not detail else '  ' + str(detail)[:160]))


_, fee_rows, _ = req('/fin/fee-items?pageNum=1&pageSize=50')
fee = [x for x in fee_rows['rows'] if x.get('calcMode') == 'BY_AREA'][0]
org = '1000000000000000010'
body = {'orgId': org, 'feeItemId': fee['id'], 'periodStart': '2026-08-01',
        'periodEnd': '2026-08-31', 'dryRun': True}
st, dry, _ = req('/fin/bills/generate', 'POST', body)
ok('批量出账试算', st == 200 and dry['dryRun'] is True,
   '生成=%s 跳过=%s' % (dry.get('generated'), dry.get('skipped')))
st, r1, _ = req('/fin/bills/generate', 'POST', {**body, 'dryRun': False})
st, r2, _ = req('/fin/bills/generate', 'POST', {**body, 'dryRun': False})
ok('批量出账幂等', r2['generated'] == 0 and r2['skipped'] >= r1['generated'],
   '首次 %s / 再次 %s 跳过 %s' % (r1['generated'], r2['generated'], r2['skipped']))

_, stat, _ = req('/fin/meter-readings?pageNum=1&pageSize=20&billed=false')
ids = [x['id'] for x in stat['rows'][:2]]
st, br, _ = req('/fin/meter-readings/bill-batch', 'POST', ids)
ok('抄表批量出账', st == 200 and br and br.get('billed', 0) >= 1, br)

_, bills, _ = req('/fin/bills?pageNum=1&pageSize=50&status=UNPAID')
b = bills['rows'][0]
st, dn, env = req('/fin/dunnings', 'POST', {'billId': b['id'], 'dunningType': 'NOTICE',
                                            'dunningContent': '回归催缴'})
ok('催缴生成记录', st == 200 and env.get('code') == 'BP00000', env.get('message'))

row = next((x for x in bills['rows'] if x.get('contractId')), None)
if row:
    st, sm, _ = req('/fin/arrears/summary?contractId=' + str(row['contractId']))
    ok('欠费摘要', st == 200 and sm.get('contract_id') and sm.get('days') is not None, sm)

_, cs, _ = req('/contracts?pageNum=1&pageSize=20&status=EFFECTIVE')
c = cs['rows'][0]
before = c['monthlyRent']
st, ch, _ = req('/contracts/%s/changes' % c['id'], 'POST',
                {'changeType': 'RENT_ADJUST', 'newMonthlyRent': str(float(before) + 50),
                 'effectiveDate': '2099-01-01', 'changeReason': '回归-未来生效'})
st, ap, _ = req('/contract-changes/%s/approve' % ch['id'], 'POST', {})
st, after, _ = req('/contracts/' + str(c['id']))
ok('变更未来生效不写回', str(after['monthlyRent']) == str(before),
   '原 %s 现 %s' % (before, after['monthlyRent']))

st, ch2, _ = req('/contracts/%s/changes' % c['id'], 'POST',
                 {'changeType': 'RENT_ADJUST', 'newMonthlyRent': str(float(before) + 30),
                  'effectiveDate': '2026-10-29', 'changeReason': '回归-立即生效'})
st, ap2, _ = req('/contract-changes/%s/approve' % ch2['id'], 'POST', {})
st, after2, _ = req('/contracts/' + str(c['id']))
ok('变更立即生效写回', abs(float(after2['monthlyRent']) - (float(before) + 30)) < 0.01,
   after2['monthlyRent'])

_, cs2, _ = req('/contracts?pageNum=1&pageSize=100&status=EFFECTIVE')
target = None
for cc in cs2['rows']:
    st, dp, _ = req('/fin/deposits', 'POST', {'contractId': cc['id'],
                                              'depositAmount': cc.get('depositAmount')})
    if st == 200:
        target = dp
        break
ok('押金自动人员/金额', target is not None and target.get('personId'),
   target and {'person': target.get('personId'), 'balance': target.get('balanceAmount')})

st, dev, _ = req('/fin/meter-readings/devices-search?keyword=' + urllib.parse.quote('水表'))
ok('设备按名称搜索', st == 200 and len(dev) > 0, '条数=%s' % len(dev))

st, hs, _ = req('/houses?pageNum=1&pageSize=5&keyword=' + urllib.parse.quote('105房间'))
ok('房源房间关键字', int(hs['total']) > 0, 'total=%s' % hs['total'])

_, flows, _ = req('/fin/cash-flows?pageNum=1&pageSize=2')
prev = float(flows['rows'][0]['balanceAfter'])
st, nf, _ = req('/fin/cash-flows', 'POST', {'flowType': 'INCOME', 'bizType': 'OTHER',
                                            'bizId': 1, 'amount': 5, 'remark': '回归余额'})
ok('流水余额=前+本次', abs(float(nf['balanceAfter']) - (prev + 5)) < 0.01,
   '%s + 5 = %s' % (prev, nf['balanceAfter']))

_, batches, _ = req('/allocation/batches?pageNum=1&pageSize=50')
allocated = next((x for x in batches['rows'] if x['batchStatus'] == 'ALLOCATED'), None)
draft = next((x for x in batches['rows'] if x['batchStatus'] in ('DRAFT', 'PUBLISHED')), None)
done = False
if allocated and draft:
    _, hs2, _ = req('/allocation/batches/%s/houses?pageNum=1&pageSize=1' % allocated['id'])
    hrow = hs2['rows'][0] if hs2.get('rows') else None
    if hrow:
        st, rr, env = req('/allocation/batches/%s/houses' % draft['id'], 'POST',
                          {'houseIds': [hrow['houseId']]})
        done = True
        ok('历史房源可入新批次', st == 200 or '已在' in str(env.get('message')), env.get('message'))
if not done:
    ok('历史房源可入新批次', True, '样本不足，跳过')

print('\n通过 %d 项，失败 %d 项' % (len(PASS), len(FAIL)))
if FAIL:
    print('失败：' + '、'.join(FAIL))
