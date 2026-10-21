# -*- coding: utf-8 -*-
"""核查剩余 9 个 ID 字段的实际值，判断是否真的需要名称"""
import json
import urllib.request

BASE = 'http://192.168.31.11:8080'
req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']


def get(p):
    r = urllib.request.Request(BASE + p, headers={
        'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600'})
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            return json.loads(x.read().decode())
    except Exception as e:
        return {'code': type(e).__name__}


CHECK = [
    ('退款', '/api/v1/fin/refunds?pageNum=1&pageSize=1',
     ['approveById', 'refundAmount', 'refundStatus']),
    ('信用', '/api/v1/credits?pageNum=1&pageSize=1',
     ['bizId', 'bizType', 'decideUserId']),
    ('申诉', '/api/v1/appeals?pageNum=1&pageSize=1', ['bizId', 'bizType']),
    ('资金流水', '/api/v1/fin/cash-flows?pageNum=1&pageSize=1',
     ['bizId', 'bizType', 'bizNo']),
    ('告警', '/api/v1/alerts?pageNum=1&pageSize=1',
     ['spaceId', 'deviceId', 'alertType', 'alertTypeLabel']),
    ('工单', '/api/v1/workorders?pageNum=1&pageSize=1',
     ['spaceId', 'houseId', 'houseIdName', 'deviceId']),
    ('通行记录', '/api/v1/access-records?pageNum=1&pageSize=1',
     ['eventId', 'houseId', 'personId']),
    ('通行授权', '/api/v1/grants?pageNum=1&pageSize=1',
     ['sourceId', 'sourceType', 'personId']),
    ('设备', '/api/v1/devices?pageNum=1&pageSize=1',
     ['tenantId', 'deviceId', 'deviceCode', 'deviceType']),
    ('催缴', '/api/v1/fin/dunnings?pageNum=1&pageSize=1', ['operatorId', 'billId']),
]

print('=' * 74)
for name, path, keys in CHECK:
    r = get(path)
    d = r.get('data')
    rows = (d.get('rows') if isinstance(d, dict) else d) or []
    f = rows[0] if rows else {}
    print('\n■ %s' % name)
    for k in keys:
        print('   %-16s = %s' % (k, str(f.get(k))[:46]))
