# -*- coding: utf-8 -*-
"""精确审计：跳过空值，列出真正缺失的枚举码与无名称的 ID"""
import json
import re
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ENDPOINTS = [
    ('申请', '/applications'), ('合同', '/contracts'), ('合同变更', '/contract-changes'),
    ('批次', '/allocation/batches'), ('配租单', '/allocation/allocations'),
    ('轮候', '/allocation/waiting'), ('年审', '/annual-reviews'),
    ('退租', '/terminations'), ('账单', '/fin/bills'), ('收款', '/fin/payments'),
    ('押金', '/fin/deposits'), ('退款', '/fin/refunds'),
    ('补贴', '/fin/subsidies/records'), ('催缴', '/fin/dunnings'),
    ('资金流水', '/fin/cash-flows'), ('计费项目', '/fin/fee-items'),
    ('工单', '/workorders'), ('告警', '/alerts'), ('投诉', '/complaints'),
    ('申诉', '/appeals'), ('信用', '/credits'), ('换房', '/exchanges'),
    ('来访', '/visits'), ('短租', '/short-rent-orders'), ('通行记录', '/access-records'),
    ('钥匙包', '/keyring'), ('通行授权', '/grants'), ('公示', '/publicities'),
    ('设备', '/devices'), ('组织', '/orgs'), ('房源', '/houses'),
    ('人员', '/persons'), ('日房态', '/house-calendar'), ('对账', '/fin/reconciles'),
]
ENUM_KEY = re.compile(r'(Status|Type|Stage|Mode|Level|Channel|Result|Source|Kind|Category)$')
ID_KEY = re.compile(r'Id$')

req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']


def call(p):
    h = {'Authorization': 'Bearer ' + TOK, 'X-Tenant-Id': '350600'}
    r = urllib.request.Request(BASE + p, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=45) as x:
            return json.loads(x.read().decode())
    except Exception as e:
        return {'code': type(e).__name__}


def is_null(v):
    return v is None or str(v) in ('None', '', 'null')


miss_enum, miss_id = {}, {}
for name, path in ENDPOINTS:
    sep = '&' if '?' in path else '?'
    r = call('/api/v1%s%spageNum=1&pageSize=3' % (path, sep))
    data = r.get('data')
    rows = (data.get('rows') if isinstance(data, dict) else data) or []
    if not rows:
        continue
    f = rows[0]
    for k, v in f.items():
        if is_null(v) or not isinstance(v, str):
            continue
        if ENUM_KEY.search(k) and k + 'Label' not in f and re.fullmatch(r'[A-Z][A-Z_0-9]+', v):
            miss_enum.setdefault(v, set()).add(k)
    for k, v in f.items():
        if ID_KEY.search(k) and k + 'Name' not in f and not is_null(v):
            miss_id.setdefault(k, set()).add(name)

print('=' * 70)
print(' ① 缺失的枚举中文（注意非空值）：%d 个编码' % len(miss_enum))
for code in sorted(miss_enum):
    print('   %-22s 字段：%s' % (code, ', '.join(sorted(miss_enum[code]))[:60]))

print('\n② 仍无名称的 ID 字段：%d 个' % len(miss_id))
for k in sorted(miss_id):
    print('   %-20s 出现于：%s' % (k, ', '.join(sorted(miss_id[k]))[:70]))
