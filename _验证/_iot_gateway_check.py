# -*- coding: utf-8 -*-
"""验证 IoT 回调网关与指令模块。"""
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request
import uuid

BASE = 'http://192.168.31.11:8080'
APP_ID = 'bp-test-app'
SECRET = 'bp-test-secret'


def sign(path, body, ts, nonce):
    canonical = 'POST' + '\n' + path + '\n' + APP_ID + '\n' + ts + '\n' + nonce + '\n' \
        + hashlib.sha256(body.encode('utf-8')).hexdigest()
    return hmac.new(SECRET.encode('utf-8'), canonical.encode('utf-8'), hashlib.sha256).hexdigest()


def post(path, payload, signed=True, ts=None, nonce=None, bad_sig=False):
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    ts = ts or str(int(time.time()))
    nonce = nonce or uuid.uuid4().hex[:16]
    headers = {'Content-Type': 'application/json', 'X-Iot-AppId': APP_ID,
               'X-Iot-Timestamp': ts, 'X-Iot-Nonce': nonce}
    if signed:
        sig = sign(path, body, ts, nonce)
        headers['X-Iot-Signature'] = ('0' * 64) if bad_sig else sig
    req = urllib.request.Request(BASE + path, data=body.encode('utf-8'),
                                 headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def login():
    body = json.dumps({'tenantCode': '350600', 'username': 'admin',
                       'password': 'admin123'}).encode()
    req = urllib.request.Request(BASE + '/api/v1/auth/login', data=body, method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600'})
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return data['data']['token']


def api(path, token, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + '/api/v1' + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600',
                                          'Authorization': 'Bearer ' + token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


device = None
token = login()
st, r = api('/devices?pageNum=1&pageSize=1', token)
rows = (r.get('data') or {}).get('rows') or []
if rows:
    device = rows[0].get('deviceId')
print('测试设备:', device)

# 1. 正常事件
ev = {'eventId': 'EV-TEST-001', 'deviceId': device or 'LK00005771',
      'identifier': 'LOW_BATTERY', 'eventLevel': 'WARN',
      'eventTime': time.strftime('%Y-%m-%d %H:%M:%S'), 'body': '{"battery":11}'}
print('1) 事件回调:', post('/api/callback/iot/event', ev))

# 2. 重复事件（新 nonce，同 eventId）
print('2) 重复事件:', post('/api/callback/iot/event', ev))

# 3. 错误签名
print('3) 错误签名:', post('/api/callback/iot/event', ev, bad_sig=True))

# 4. 过期时间戳
print('4) 过期时间戳:', post('/api/callback/iot/event', ev,
                              ts=str(int(time.time()) - 3600)))

# 5. 心跳
print('5) 心跳:', post('/api/callback/iot/heartbeat',
                       [{'deviceId': device or 'LK00005771', 'online': True,
                         'battery': 88, 'rssi': '-61',
                         'reportTime': time.strftime('%Y-%m-%d %H:%M:%S')}]))

# 6. 上下线
print('6) 上下线:', post('/api/callback/iot/device-status',
                         {'deviceId': device or 'LK00005771', 'status': 'OFFLINE',
                          'reason': 'NETWORK',
                          'time': time.strftime('%Y-%m-%d %H:%M:%S')}))

# 7. 告警恢复
print('7) 告警恢复:', post('/api/callback/iot/alarm-ack',
                           {'eventId': 'EV-TEST-001', 'recovered': True,
                            'recoverTime': time.strftime('%Y-%m-%d %H:%M:%S')}))

# 8. 指令：远程开锁
st, r = api('/dev-commands', token, 'POST',
            {'commandType': 'LOCK_OPEN', 'deviceId': device, 'reason': '联调验证开锁'})
print('8) 创建开锁指令:', st, (r.get('data') or {}).get('status'),
      (r.get('data') or {}).get('requestId'))
req_id = (r.get('data') or {}).get('requestId')

# 9. 指令回执（模拟 IoT 回调）
if req_id:
    print('9) 指令回执:', post('/api/callback/iot/command/ack',
                               {'requestId': req_id, 'lockId': device, 'code': '0',
                                'message': 'ok', 'costMs': 210,
                                'deviceTime': time.strftime('%Y-%m-%d %H:%M:%S')}))

# 10. 指令列表
st, r = api('/dev-commands?pageNum=1&pageSize=5', token)
print('10) 指令列表 total:', (r.get('data') or {}).get('total'))
for x in ((r.get('data') or {}).get('rows') or [])[:2]:
    print('   ', x.get('commandNo'), x.get('commandType'), x.get('status'),
          x.get('resultCode'))
