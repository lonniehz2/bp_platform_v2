# -*- coding: utf-8 -*-
"""拉闸安全策略 + 联调工具接口验证。"""
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOKEN = None


def call(path, method='GET', payload=None, full=False):
    data = json.dumps(payload).encode() if payload is not None else None
    url = (BASE + path) if full else (BASE + '/api/v1' + path)
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600',
                                          'Authorization': 'Bearer ' + (TOKEN or '')})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def login():
    global TOKEN
    req = urllib.request.Request(BASE + '/api/v1/auth/login',
                                 data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                                                  'password': 'admin123'}).encode(),
                                 method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600'})
    TOKEN = json.loads(urllib.request.urlopen(req, timeout=30).read())['data']['token']


login()

# 1) 签名自测
body = '{"eventId":"EV-SIGN-1","deviceId":"LK1","identifier":"LOW_BATTERY"}'
ts, nonce = '1793029200', 'a1b2c3d4e5f6'
st, r = call('/iot/sign-preview', 'POST',
             {'action': 'event', 'appId': 'bp-test-app', 'appSecret': 'bp-test-secret',
              'timestamp': ts, 'nonce': nonce, 'body': body})
d = r.get('data') or {}
canonical = 'POST\n/api/callback/iot/event\nbp-test-app\n' + ts + '\n' + nonce + '\n' \
    + hashlib.sha256(body.encode()).hexdigest()
expect = hmac.new(b'bp-test-secret', canonical.encode(), hashlib.sha256).hexdigest()
print('1) 签名自测:', st, '接口签名==本地签名:', d.get('signature') == expect)

# 2) 回调日志
st, r = call('/iot/callback-logs?pageNum=1&pageSize=5')
print('2) 回调日志 total:', (r.get('data') or {}).get('total'))

# 3) 放宽参数用于测试
for k, v in [('iot.meter.switch.arrearsThreshold', '0'),
             ('iot.meter.switch.overdueDays', '0'),
             ('iot.meter.switch.delayMinutes', '10'),
             ('iot.meter.switch.nightFrom', '03:00'),
             ('iot.meter.switch.nightTo', '04:00')]:
    call('/sys/configs', 'POST', {'key': k, 'value': v, 'description': '联调测试'})

# 4) 创建拉闸（延迟 10 分钟）
st, r = call('/dev-commands', 'POST',
             {'commandType': 'METER_SWITCH', 'deviceId': 'LK00005771',
              'reason': '联调：欠费拉闸测试'})
cmd = r.get('data') or {}
print('4) 建拉闸:', st, cmd.get('status'), '审批:', cmd.get('approveStatus'),
      '执行时间:', cmd.get('executeAfter'), '欠费:', cmd.get('arrearsAmount'))

# 5) 审批通过（未到点，应保持 PENDING）
if cmd.get('id'):
    st, r = call('/dev-commands/%s/approve?approve=true' % cmd['id'], 'POST')
    c2 = r.get('data') or {}
    print('5) 审批通过:', st, c2.get('status'), c2.get('approveStatus'))

    # 6) 撤销
    st, r = call('/dev-commands/%s/cancel' % cmd['id'], 'POST')
    print('6) 撤销:', st, (r.get('data') or {}).get('status'))

# 7) 延迟 0 分钟 → 审批后立即下发
call('/sys/configs', 'POST', {'key': 'iot.meter.switch.delayMinutes', 'value': '0',
                              'description': '联调测试'})
st, r = call('/dev-commands', 'POST',
             {'commandType': 'METER_SWITCH', 'deviceId': 'LK00005771',
              'reason': '联调：立即拉闸'})
cmd2 = r.get('data') or {}
if cmd2.get('id'):
    st, r = call('/dev-commands/%s/approve?approve=true' % cmd2['id'], 'POST')
    c3 = r.get('data') or {}
    print('7) 立即执行:', st, c3.get('status'), c3.get('resultCode'), c3.get('approveStatus'))

# 8) 恢复默认参数
for k, v in [('iot.meter.switch.arrearsThreshold', '0.01'),
             ('iot.meter.switch.overdueDays', '30'),
             ('iot.meter.switch.delayMinutes', '10'),
             ('iot.meter.switch.nightFrom', '22:00'),
             ('iot.meter.switch.nightTo', '07:00')]:
    call('/sys/configs', 'POST', {'key': k, 'value': v, 'description': '默认值'})
print('8) 参数已恢复默认')

# 9) 重放一条回调日志
st, r = call('/iot/callback-logs?pageNum=1&pageSize=1&processStatus=DONE')
rows = (r.get('data') or {}).get('rows') or []
if rows:
    st, r = call('/iot/callback-logs/%s/replay' % rows[0]['id'], 'POST')
    print('9) 重放:', st, (r.get('data') or {}).get('code'))
