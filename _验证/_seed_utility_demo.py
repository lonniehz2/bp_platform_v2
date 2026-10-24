# -*- coding: utf-8 -*-
"""水电燃气演示数据：计费项 → 设备绑定 → 基线读数 → 出账 → 账单。

跑完后「抄表管理」可看到水/电/燃气三类记录，「账单与缴费」能看到对应账单。
"""
import json
import urllib.error
import urllib.request
from datetime import date, timedelta

B = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'


def call(p, m='GET', body=None, tok=None):
    d = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(B + p, data=d, method=m)
    r.add_header('Content-Type', 'application/json')
    r.add_header('X-Tenant-Id', TENANT)
    if tok:
        r.add_header('Authorization', 'Bearer ' + tok)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def login(u, p):
    r = urllib.request.Request(
        B + '/auth/login',
        data=json.dumps({'tenantCode': TENANT, 'username': u, 'password': p}).encode(),
        method='POST', headers={'Content-Type': 'application/json', 'X-Tenant-Id': TENANT})
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.loads(x.read().decode())['data']['token']


tok = login('admin', 'admin123')
rows = lambda d: (d or {}).get('rows') or []

# ---------- 1) 计费项：水费 / 燃气费 ----------
items = rows(call('/fin/fee-items?pageNum=1&pageSize=100', tok=tok)[1]['data'])
def find_item(name):
    return next((x for x in items if x.get('itemName') == name), None)

WANT = [
    ('WATER-P1', '一期水费', '3.50', '吨'),
    ('GAS-P1', '一期燃气费', '2.80', '方'),
]
created_items = {}
for code, name, price, unit in WANT:
    hit = find_item(name)
    if hit:
        created_items[name] = hit
        print('已存在计费项:', name, hit.get('unitPrice'), '元/' + (hit.get('unit') or unit))
        continue
    st, r = call('/fin/fee-items', 'POST', {
        'itemCode': code, 'itemName': name, 'itemType': 'ENERGY', 'calcMode': 'METER',
        'unitPrice': float(price), 'unit': unit, 'status': 'ENABLED'}, tok)
    d = (r or {}).get('data') or {}
    print('新建计费项:', st, (r or {}).get('code'), name, d.get('unitPrice'), '元/' + unit)
    if d:
        created_items[name] = d

# 电费沿用已有
elec = find_item('一期电费')
if elec:
    created_items['一期电费'] = elec

# ---------- 2) 房源与设备 ----------
orgs = rows(call('/orgs?pageNum=1&pageSize=100', tok=tok)[1]['data'])
oid = next(o['id'] for o in orgs if o['orgName'] == '一期示范小区')
house = {'id': 1000000000000000623, 'houseCode': 'ZZ-H-00001'}
print('目标房源:', house.get('houseCode'), house.get('id'))

devs = rows(call('/devices?pageNum=1&pageSize=200&spaceId=%s' % house.get('spaceId'),
                tok=tok)[1]['data']) if house.get('spaceId') else []
print('该房源已绑设备:', [(d.get('deviceName'), d.get('deviceType')) for d in devs][:5])

# ---------- 3) 基线读数 + 本期读数 ----------
DEV = {'WATER-P1': 'DEMO-METER-WATER', 'GAS-P1': 'DEMO-METER-GAS',
       'ELEC-P1': 'DEMO-METER-ELEC'}
BASE = {  # 计费项名 → (基线, 本期)
    '一期电费': (12000, 12350),
    '一期水费': (350, 372),
    '一期燃气费': (80, 96),
}
today = date.today()
prev = today - timedelta(days=30)

made = []
for name, (b0, b1) in BASE.items():
    item = created_items.get(name)
    if not item:
        print('跳过（无计费项）:', name)
        continue
    # 基线
    call('/fin/meter-readings', 'POST', {
        'houseId': house['id'], 'feeItemId': item['id'], 'reading': b0,
        'readDate': str(prev), 'deviceId': DEV[item.get('itemCode','')]}, tok)
    # 本期
    st, r = call('/fin/meter-readings', 'POST', {
        'houseId': house['id'], 'feeItemId': item['id'], 'reading': b1,
        'readDate': str(today), 'deviceId': DEV[item.get('itemCode','')]}, tok)
    d = (r or {}).get('data') or {}
    usage = float(b1) - float(b0)
    amount = usage * float(item.get('unitPrice') or 0)
    print('读数 %s: %s 基线 %s → 本期 %s，用量 %s，应收 %.2f'
          % (name, (r or {}).get('code'), b0, b1, usage, amount))
    if d.get('id'):
        st2, r2 = call('/fin/meter-readings/%s/bill' % d['id'], 'POST', None, tok)
        bill = (r2 or {}).get('data') or {}
        print('   出账:', st2, (r2 or {}).get('code'), bill.get('billNo'),
              '金额', bill.get('payableAmount'))
        made.append((name, usage, amount, bill.get('billNo')))

print('\n=== 汇总 ===')
for name, usage, amount, no in made:
    print('%-10s 用量 %-8s 金额 %-8.2f 账单 %s' % (name, usage, amount, no))
