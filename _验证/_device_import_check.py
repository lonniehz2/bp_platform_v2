# -*- coding: utf-8 -*-
"""设备导入接口验证（multipart）。"""
import io
import json
import urllib.request
import uuid

BASE = 'http://192.168.31.11:8080/api/v1'
r = urllib.request.Request(BASE + '/auth/login',
                           data=json.dumps({'tenantCode': '350600', 'username': 'admin',
                                            'password': 'admin123'}).encode(),
                           method='POST',
                           headers={'Content-Type': 'application/json', 'X-Tenant-Id': '350600'})
tok = json.loads(urllib.request.urlopen(r, timeout=30).read())['data']['token']
uid = uuid.uuid4().hex[:6].upper()
csv = ('设备编号,设备名称,设备类型,设备MAC,房源编号\n'
       'IMP-%s-1,导入门锁1,门锁,AA:BB:CC:00:00:01,H8063501\n'
       'IMP-%s-2,导入电表2,电表,AA:BB:CC:00:00:02,\n'
       'IMP-%s-1,重复编号,门锁,AA:BB:CC:00:00:03,\n'
       'IMP-%s-3,未知类型,机器人,,\n') % (uid, uid, uid, uid)

boundary = '----dshboundary'
body = io.BytesIO()
body.write(('--%s\r\nContent-Disposition: form-data; name="file"; filename="dev.csv"\r\n'
            'Content-Type: text/csv\r\n\r\n' % boundary).encode())
body.write(csv.encode('utf-8'))
body.write(('\r\n--%s--\r\n' % boundary).encode())

req = urllib.request.Request(BASE + '/devices/import', data=body.getvalue(), method='POST',
                             headers={'Authorization': 'Bearer ' + tok,
                                      'X-Tenant-Id': '350600',
                                      'Content-Type': 'multipart/form-data; boundary=' + boundary})
res = json.loads(urllib.request.urlopen(req, timeout=120).read())
d = res.get('data') or {}
print('结果:', {k: d.get(k) for k in ('total', 'created', 'skipped')})
for e in d.get('errors') or []:
    print(' 行', e.get('line'), e.get('message'))
