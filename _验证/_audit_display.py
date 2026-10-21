# -*- coding: utf-8 -*-
"""客观审计：遍历所有列表接口，检查是否还有「裸 ID」「英文枚举」未被补全"""
import json
import re
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None
D = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json', encoding='utf-8'))
ORG = D['orgId']

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
CN = re.compile(r'[\u4e00-\u9fa5]')


def call(m, p):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    r = urllib.request.Request(BASE + p, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=45) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return {'code': type(e).__name__}


TOK = call('POST', '/api/v1/auth/login')  # placeholder
req = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': '350600', 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())['data']['token']

print('=' * 74)
print(' 显示层审计：仍会露出英文编码/裸 ID 的接口')
print('=' * 74)

bad_enum, bad_id = [], []
for name, path in ENDPOINTS:
    sep = '&' if '?' in path else '?'
    r = call('GET', '/api/v1%s%spageNum=1&pageSize=3' % (path, sep))
    data = r.get('data')
    rows = (data.get('rows') if isinstance(data, dict) else data) or []
    if not rows:
        continue
    first = rows[0]
    for k, v in first.items():
        if not isinstance(v, str):
            continue
        if ENUM_KEY.search(k) and k + 'Label' not in first:
            # 是否是纯英文编码（全大写+下划线）
            if re.fullmatch(r'[A-Z][A-Z_0-9]+', v):
                bad_enum.append((name, k, v))
    # 裸 ID：有 xxxId 但没有 xxxIdName
    for k, v in first.items():
        if ID_KEY.search(k) and k + 'Name' not in first:
            bad_id.append((name, k, str(v)[:12]))

print('\n① 枚举值未补 Label：%d 处' % len(bad_enum))
for n, k, v in bad_enum[:20]:
    print('   %-10s %-24s %s' % (n, k, v))

print('\n② ID 未补 Name：%d 处' % len(bad_id))
seen = set()
for n, k, v in bad_id:
    key = (n, k)
    if key in seen:
        continue
    seen.add(key)
    print('   %-10s %-24s %s...' % (n, k, v))

print('\n合计待处理：枚举 %d ｜ ID %d' % (len(set((a, b) for a, b, _ in bad_enum)),
                                     len(seen)))
