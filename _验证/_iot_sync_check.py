# -*- coding: utf-8 -*-
"""设备同步 / 表计拉取 / 告警转工单 验证。"""
import json
import time
import urllib.error
import urllib.request

import pymysql

BASE = 'http://192.168.31.11:8080'
TOKEN = None


def call(path, method='GET', payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + '/api/v1' + path, data=data, method=method,
                                 headers={'Content-Type': 'application/json',
                                          'X-Tenant-Id': '350600',
                                          'Authorization': 'Bearer ' + (TOKEN or '')})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
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


def sign(path, body, ts, nonce):
    import hashlib
    import hmac
    canonical = 'POST\n' + path + '\nbp-test-app\n' + ts + '\n' + nonce + '\n' \
        + hashlib.sha256(body.encode()).hexdigest()
    return hmac.new(b'bp-test-secret', canonical.encode(), hashlib.sha256).hexdigest()


def callback(action, payload):
    import uuid
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    ts = str(int(time.time()))
    nonce = uuid.uuid4().hex[:16]
    path = '/api/callback/iot/' + action
    req = urllib.request.Request(BASE + path, data=body.encode(), method='POST',
                                 headers={'Content-Type': 'application/json',
                                          'X-Iot-AppId': 'bp-test-app',
                                          'X-Iot-Timestamp': ts,
                                          'X-Iot-Nonce': nonce,
                                          'X-Iot-Signature': sign(path, body, ts, nonce)})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}


login()

# 1) 设备同步（mock 返回空）
st, r = call('/iot/devices/sync?days=1', 'POST')
print('1) 设备同步:', st, r.get('data'))

# 2) 表计拉取（mock 返回空）
st, r = call('/iot/meter/pull', 'POST')
print('2) 表计拉取:', st, r.get('data'))

# 3) 表计上报入库（ELEC）
st, r = callback('meter', [{'meterNo': 'LK00005771', 'deviceId': 'LK00005771',
                            'meterType': 'ELEC', 'reading': 1234.5,
                            'readTime': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'PUSH'}])
print('3) 表计上报:', st, r)

# 4) 严重告警 → 自动工单
st, r = callback('event', {'eventId': 'EV-AUTO-WO-001', 'deviceId': 'LK00005771',
                           'identifier': 'DURESS', 'eventLevel': 'CRITICAL',
                           'eventTime': time.strftime('%Y-%m-%d %H:%M:%S'),
                           'body': '{"pwdId":"1001"}'})
print('4) 严重告警:', st, r)

time.sleep(1)
db = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                     database='bp_platform', charset='utf8mb4', autocommit=True,
                     connect_timeout=20, read_timeout=120)
cur = db.cursor()
cur.execute("select workorder_no,order_title,order_type,order_status,device_id "
            "from bp_ops_workorder where device_id='LK00005771' order by create_time desc limit 3")
print('5) 自动工单:')
for row in cur.fetchall():
    print('   ', row)
cur.execute("select count(*) from bp_fin_meter_reading where device_id='LK00005771'")
print('6) 表计读数条数:', cur.fetchone()[0])
db.close()
