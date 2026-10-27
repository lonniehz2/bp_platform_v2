# -*- coding: utf-8 -*-
"""本轮 7 项接口验证。"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080/api/v1'
r = urllib.request.Request(BASE + '/auth/login',
                           data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                                            'password': 'admin123'}).encode(),
                           method='POST',
                           headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
TOKEN = json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']


def call(path, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600',
                                          'Authorization': 'Bearer ' + TOKEN})
    try:
        with urllib.request.urlopen(req, timeout=120) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


# 1) 配租单人员姓名/手机
st, r = call('/allocation/allocations?pageNum=1&pageSize=3&batchId=373398249891041280')
rows = (r.get('data') or {}).get('rows') or []
print('1) 配租单字段:', [(x.get('personName'), x.get('phoneMask')) for x in rows][:3])

# 2) 摇号结果姓名/手机
st, r = call('/allocation/lottery/373398249891041280')
res = (r.get('data') or [])[:2]
print('2) 结果字段:', [(x.get('personName'), x.get('phoneMask'), x.get('resultType')) for x in res])

# 3) 生成配租单（重复调用，应给“已生成”提示）
st, r = call('/allocation/batches/373398249891041280/generate-allocations', 'POST', {})
print('3) 生成提示:', st, r.get('data'))

# 4) 房源状态
st, r = call('/houses?pageNum=1&pageSize=3&orgId=371689292805836800&houseStatus=LOCKED')
print('4) LOCKED 房源数:', (r.get('data') or {}).get('total'))

# 5) 公示中签名单
st, r = call('/publicities?pageNum=1&pageSize=5')
pubs = (r.get('data') or {}).get('rows') or []
pub = next((x for x in pubs if x.get('batchId')), None)
print('5) 公示:', pub and pub.get('id'), pub and pub.get('batchId'))
if pub:
    st, r = call('/publicities/%s/winners' % pub['id'])
    ws = (r.get('data') or [])
    print('   中签数:', len(ws), '示例:', [(w.get('personName'), w.get('houseName'),
                                            w.get('lotterySeq'), w.get('resultTypeLabel'))
                                           for w in ws[:3]])

# 6) 公示天数参数可改
st, r = call('/sys/configs/biz.publicity.allocation.minDays')
print('6) 当前公示天数:', st, r.get('data'))
st, r = call('/sys/configs', 'POST', {'key': 'biz.publicity.allocation.minDays', 'value': '7'})
print('   写回:', st, (r.get('data') or {}).get('configValue'))
