# -*- coding: utf-8 -*-
"""凭据同步验证：新增钥匙 → 生成凭据同步记录。"""
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

st, r = call('/persons?pageNum=1&pageSize=1')
personId = ((r.get('data') or {}).get('rows') or [{}])[0].get('id')
print('测试人员:', personId)

st, r = call('/keyring', 'POST', {'personId': personId, 'keyType': 'PASSWORD',
                                  'channelValue': 'PWD-' + str(int(time.time())),
                                  'keyAlias': '联调验证密码', 'verifyWay': 'PASSWORD', 'expireTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()+86400*30))})
key = r.get('data') or {}
print('新增钥匙:', st, key.get('id'), key.get('keyType'), key.get('keyStatus'))

if key.get('id'):
    st, r = call('/keyring/%s/freeze' % key['id'], 'POST')
    print('冻结:', st, (r.get('data') or {}).get('keyStatus'))
    st, r = call('/keyring/%s/remove' % key['id'], 'POST')
    print('删除:', st)

time.sleep(1)
db = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                     database='bp_platform', charset='utf8mb4', autocommit=True,
                     connect_timeout=20, read_timeout=120)
cur = db.cursor()
cur.execute("select action,status,key_type,error_msg from bp_iot_credential_sync "
            "order by create_time desc limit 5")
print('同步记录:')
for row in cur.fetchall():
    print('   ', row)
db.close()

st, r = call('/iot/credential-sync?pageNum=1&pageSize=5')
print('接口返回 total:', (r.get('data') or {}).get('total'))
