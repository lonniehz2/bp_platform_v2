# -*- coding: utf-8 -*-
"""验证表计倍率：multiplier=10 时用量 =（差值）×10。"""
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
    canonical = ('POST\n' + path + '\n' + APP_ID + '\n' + ts + '\n' + nonce + '\n'
                 + hashlib.sha256(body.encode('utf-8')).hexdigest())
    return hmac.new(SECRET.encode('utf-8'), canonical.encode('utf-8'),
                    hashlib.sha256).hexdigest()


def post(path, payload):
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex[:16]
    headers = {'Content-Type': 'application/json', 'X-Iot-AppId': APP_ID,
               'X-Iot-Timestamp': ts, 'X-Iot-Nonce': nonce,
               'X-Iot-Signature': sign(path, body, ts, nonce)}
    req = urllib.request.Request(BASE + path, data=body.encode('utf-8'),
                                 headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, json.loads(r.read().decode())


def login():
    body = json.dumps({'tenantCode': '350600', 'username': 'admin',
                       'password': 'admin123'}).encode()
    req = urllib.request.Request(BASE + '/api/v1/auth/login', data=body, method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600'})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())['data']['token']


TOKEN = login()
DEVICE = 'DEMO-ELEC-00001'

for d, reading in [('2026-09-01 08:00:00', 100), ('2026-09-02 08:00:00', 110)]:
    st, r = post('/api/callback/iot/meter', {
        'meterNo': DEVICE, 'deviceId': DEVICE, 'meterType': 'ELEC',
        'reading': reading, 'multiplier': 10, 'unit': 'kWh',
        'readTime': d, 'source': 'PUSH'
    })
    print(d, st, r.get('code'), r.get('message'))

q = urllib.request.Request(
    BASE + '/api/v1/fin/meter-readings?pageNum=1&pageSize=10&deviceId=' + DEVICE,
    headers={'Authorization': 'Bearer ' + TOKEN, 'X-Tenant-Id': '350600'})
rows = json.loads(urllib.request.urlopen(q, timeout=30).read())['data']['rows']
print('读数条数:', len(rows))
for x in rows[:4]:
    print(' ', x.get('readDate'), 'reading=', x.get('reading'),
          'multiplier=', x.get('multiplier'), 'usage=', x.get('usageAmount'),
          'unit=', x.get('unit'))
