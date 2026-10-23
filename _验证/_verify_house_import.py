# -*- coding: utf-8 -*-
"""验证房源批量导入：正常行 + 异常行（组织不存在/编号重复/列数不足）。"""
import io
import json
import urllib.error
import urllib.request
import uuid

API = 'http://192.168.31.11:8080/api/v1'
TENANT = '350600'


def login():
    r = urllib.request.Request(
        API + '/auth/login',
        data=json.dumps({'tenantCode': TENANT, 'username': 'admin',
                         'password': 'admin123'}).encode(),
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Tenant-Id': TENANT})
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())['data']['token']


def get(path, tok):
    r = urllib.request.Request(API + path, headers={'Authorization': 'Bearer ' + tok,
                                                    'X-Tenant-Id': TENANT})
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.loads(x.read().decode())


def upload(content, tok):
    boundary = '----dsh' + uuid.uuid4().hex
    body = io.BytesIO()
    body.write(('--%s\r\n' % boundary).encode())
    body.write(b'Content-Disposition: form-data; name="file"; filename="houses.csv"\r\n')
    body.write(b'Content-Type: text/csv\r\n\r\n')
    body.write(content.encode('utf-8'))
    body.write(('\r\n--%s--\r\n' % boundary).encode())
    data = body.getvalue()
    r = urllib.request.Request(API + '/houses/import', data=data, method='POST')
    r.add_header('Content-Type', 'multipart/form-data; boundary=' + boundary)
    r.add_header('Authorization', 'Bearer ' + tok)
    r.add_header('X-Tenant-Id', TENANT)
    try:
        with urllib.request.urlopen(r, timeout=60) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


tok = login()

# 取一期小区的组织编码与一个房间空间编码
orgs = get('/orgs?pageNum=1&pageSize=100', tok)['data']['rows']
org = next((o for o in orgs if o['orgName'] == '一期示范小区'), None)
tree = get('/spaces/tree?orgId=%s' % org['id'], tok)['data']
flat = []


def walk(ns):
    for n in ns or []:
        flat.append(n)
        walk(n.get('children'))


walk(tree if isinstance(tree, list) else (tree or {}).get('rows'))
room = next((x for x in flat if x.get('spaceType') == 'ROOM'), None)
print('组织编码=%s 房间编码=%s' % (org['orgCode'], room['spaceCode']))

tag = uuid.uuid4().hex[:6].upper()
csv = '\n'.join([
    'ORGANIZATION_CODE,SPACE_CODE,HOUSE_CODE,HOUSE_NAME,HOUSE_TYPE,USE_TYPE,AREA,RENT,RENT_UNIT,STATUS',
    '%s,%s,IMP-%s-1,导入测试房1,PUBLIC_RENTAL,CIVIL,55,15,AREA_MONTH,VACANT'
    % (org['orgCode'], room['spaceCode'], tag),
    '%s,%s,IMP-%s-2,导入测试房2,PUBLIC_RENTAL,CIVIL,60,15,AREA_MONTH,VACANT'
    % (org['orgCode'], room['spaceCode'], tag),
    '%s,%s,IMP-%s-1,重复编号房,PUBLIC_RENTAL,CIVIL,50,15,AREA_MONTH,VACANT'
    % (org['orgCode'], room['spaceCode'], tag),
    'NOT-EXIST,%s,IMP-%s-3,组织不存在房,PUBLIC_RENTAL,CIVIL,50,15,AREA_MONTH,VACANT'
    % (room['spaceCode'], tag),
    'only,two',
])

st, r = upload(csv, tok)
d = (r or {}).get('data') or {}
print('导入结果：HTTP %s %s' % (st, (r or {}).get('code')))
print('  总行数 %s，成功 %s，跳过 %s' % (d.get('total'), d.get('created'), d.get('skipped')))
for e in (d.get('errors') or []):
    print('  行 %s：%s' % (e.get('line'), e.get('message')))

# 校验落库
listed = get('/houses?pageNum=1&pageSize=20&keyword=IMP-%s' % tag, tok)['data']
print('落库查询：命中 %s 套' % listed.get('total'))
