# -*- coding: utf-8 -*-
"""round4 回归：合同承租人信息、一房一租、批次历史房源、变更、押金、抄表账单。"""
import json
import urllib.error
import urllib.request

B = 'http://192.168.31.11:8080/api/v1'
H = {'X-Tenant-Id': '350600'}


def login():
    r = urllib.request.Request(B + '/auth/login',
                               data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                                                'password': 'admin123'}).encode(),
                               method='POST',
                               headers={'Content-Type': 'application/json',
                                        'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']


H['Authorization'] = 'Bearer ' + login()


def call(p, m='GET', b=None):
    d = json.dumps(b).encode() if b is not None else (b'' if m == 'POST' else None)
    x = urllib.request.Request(B + p, data=d, method=m,
                               headers={**H, 'Content-Type': 'application/json'})
    try:
        y = urllib.request.urlopen(x, timeout=60)
        return y.status, json.loads(y.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


# 1) 新建合同只传 personId，检查姓名/手机/证件
st, r = call('/persons?pageNum=1&pageSize=1')
p = r['data']['rows'][0]
st, r = call('/houses?pageNum=1&pageSize=50&houseStatus=AVAILABLE')
h = r['data']['rows'][0]
body = {'contractType': 'PUBLIC_RENTAL', 'orgId': h['orgId'], 'lessorOrgId': h['orgId'], 'spaceId': h.get('spaceId'), 'rentPrice': 30,
        'lesseePersonId': p['id'], 'houseId': h['id'],
        'leaseStart': '2026-11-01', 'leaseEnd': '2027-10-31',
        'monthlyRent': 1000, 'depositAmount': 1000, 'payCycle': 'MONTH', 'payDay': 1}
st, r = call('/contracts', 'POST', body)
d = r.get('data') or {}
print('1 合同承租人:', st, 'name=', d.get('lesseeName'), 'phone=', d.get('lesseePhone'),
      'idcard=', d.get('lesseeIdCardMask'), r.get('message') or '')

# 2) 一房一租：同房源再签
st, r = call('/contracts', 'POST', {**body, 'lesseePersonId': p['id']})
print('2 一房一租:', st, r.get('message'))

# 3) 合同变更：入口对应的接口
if d.get('id'):
    st, r = call('/contracts/' + d['id'] + '/changes', 'POST',
                 {'changeType': 'RENT_ADJUST', 'newMonthlyRent': 1200,
                  'effectiveDate': '2026-10-29', 'changeReason': '回归调租'})
    ch = r.get('data') or {}
    print('3 变更创建:', st, ch.get('changeNo'), ch.get('approveStatus'))
    if ch.get('id'):
        st, r = call('/contract-changes/' + str(ch['id']) + '/approve', 'POST', {})
        print('3 变更批准:', st, (r.get('data') or {}).get('approveStatus'))
        st, r = call('/contracts/' + d['id'])
        print('3 合同月租写回:', (r.get('data') or {}).get('monthlyRent'))

# 4) 押金：不传人员、不传已收
st, r = call('/contracts?pageNum=1&pageSize=50&status=EFFECTIVE')
cs = [c for c in (r['data']['rows'] if isinstance(r.get('data'), dict) else [])]
print('4 押金测试:', end=' ')
if cs:
    st, r = call('/fin/deposits', 'POST', {'contractId': cs[0]['id'],
                                            'depositAmount': cs[0].get('depositAmount')})
    print(st, (r.get('data') or {}).get('personId'), r.get('message'))
