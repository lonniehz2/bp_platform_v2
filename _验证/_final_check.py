# -*- coding: utf-8 -*-
"""最终全量核对：46 项页面 + 7 个新模块数据 + 关键闭环指标"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': '350600'}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=45) as x:
            return x.status, json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}
    except Exception as e:
        return -1, {'code': type(e).__name__}


ORG = json.load(open(r'D:\Work\业务平台开发\_验证\_test_data.json',
                     encoding='utf-8'))['orgId']
TOK = call('POST', '/api/v1/auth/login',
           {'tenantId': '350600', 'username': 'admin', 'password': 'admin123'}
           )[1].get('data', {}).get('token')

PAGES = [
    ('运营驾驶舱', '/api/v1/rpt/screens/OVERVIEW/data'),
    ('指标', '/api/v1/rpt/metrics/current'),
    ('组织机构', '/api/v1/orgs?pageNum=1&pageSize=5'),
    ('空间树', '/api/v1/spaces/tree?orgId=%s' % ORG),
    ('房源', '/api/v1/houses?pageNum=1&pageSize=5'),
    ('人员', '/api/v1/persons?pageNum=1&pageSize=5'),
    ('保障档案', '/api/v1/guarantee-profiles?pageNum=1&pageSize=5'),
    ('实名认证', '/api/v1/verify-records?pageNum=1&pageSize=5'),
    ('申请', '/api/v1/applications?pageNum=1&pageSize=5'),
    ('公示', '/api/v1/publicities?pageNum=1&pageSize=5'),
    ('轮候', '/api/v1/allocation/waiting?pageNum=1&pageSize=5'),
    ('批次', '/api/v1/allocation/batches?pageNum=1&pageSize=5'),
    ('配租单', '/api/v1/allocation/allocations?pageNum=1&pageSize=5'),
    ('合同', '/api/v1/contracts?pageNum=1&pageSize=5'),
    ('合同变更', '/api/v1/contract-changes?pageNum=1&pageSize=5'),
    ('年审', '/api/v1/annual-reviews?pageNum=1&pageSize=5'),
    ('退租', '/api/v1/terminations?pageNum=1&pageSize=5'),
    ('账单', '/api/v1/fin/bills?pageNum=1&pageSize=5'),
    ('收款', '/api/v1/fin/payments?pageNum=1&pageSize=5'),
    ('押金', '/api/v1/fin/deposits?pageNum=1&pageSize=5'),
    ('退款', '/api/v1/fin/refunds?pageNum=1&pageSize=5'),
    ('补贴', '/api/v1/fin/subsidies/records?pageNum=1&pageSize=5'),
    ('计费项目', '/api/v1/fin/fee-items?pageNum=1&pageSize=5'),
    ('催缴', '/api/v1/fin/dunnings?pageNum=1&pageSize=5'),
    ('资金流水', '/api/v1/fin/cash-flows?pageNum=1&pageSize=5'),
    ('对账', '/api/v1/fin/reconciles?pageNum=1&pageSize=5'),
    ('工单', '/api/v1/workorders?pageNum=1&pageSize=5'),
    ('告警', '/api/v1/alerts?pageNum=1&pageSize=5'),
    ('规则集', '/api/v1/rules/rulesets'),
    ('设备', '/api/v1/devices?pageNum=1&pageSize=5'),
    ('通行记录', '/api/v1/access-records?pageNum=1&pageSize=5'),
    ('消息待办', '/api/v1/messages/todos?pageNum=1&pageSize=5'),
    ('报表', '/api/v1/rpt/reports'),
    ('大屏', '/api/v1/rpt/screens'),
    ('钥匙包', '/api/v1/keyring?pageNum=1&pageSize=5'),
    ('授权', '/api/v1/grants?pageNum=1&pageSize=5'),
    ('对账差异', '/api/v1/grant-reconcile/diffs?pageNum=1&pageSize=5'),
    ('用户权限', '/api/v1/rbac/users?pageNum=1&pageSize=5'),
    ('审计日志', '/api/v1/sys/audit-logs?pageNum=1&pageSize=5'),
    ('字典', '/api/v1/sys/dicts/HOUSE_TYPE'),
    ('系统参数', '/api/v1/sys/configs'),
    ('开放应用', '/api/v1/open/apps'),
    ('开放接口', '/api/v1/open/apis'),
    ('监管报送', '/api/v1/gov/reports?pageNum=1&pageSize=5'),
    ('政务适配器', '/api/v1/gov/adapters'),
    ('短租订单', '/api/v1/short-rent-orders?pageNum=1&pageSize=5'),
    ('申诉', '/api/v1/appeals?pageNum=1&pageSize=5'),
    ('信用', '/api/v1/credits?pageNum=1&pageSize=5'),
    ('换房', '/api/v1/exchanges?pageNum=1&pageSize=5'),
    ('投诉', '/api/v1/complaints?pageNum=1&pageSize=5'),
]

print('=' * 74)
print(' 最终全量核对（%d 项）' % len(PAGES))
print('=' * 74)
fail, empty, okc = [], [], 0
for name, path in PAGES:
    st, r = call('GET', path)
    if st != 200 or r.get('code') != 'BP00000':
        fail.append((name, r.get('code'), str(r.get('message'))[:44]))
        print('  ✗ %-12s %s' % (name, r.get('code')))
        continue
    d = r.get('data')
    if isinstance(d, dict):
        n = d.get('total')
        n = int(n) if n not in (None, '') else len(d.get('rows') or d.get('widgets') or [])
    elif isinstance(d, list):
        n = len(d)
    else:
        n = 1 if d else 0
    if n and n > 0:
        okc += 1
        print('  ✓ %-12s %s' % (name, n))
    else:
        empty.append(name)
        print('  ○ %-12s 空' % name)

print('-' * 74)
print(' 有数据 %d ｜ 空 %d ｜ 失败 %d' % (okc, len(empty), len(fail)))
if empty:
    print(' 空清单：%s' % ', '.join(empty))
if fail:
    for x in fail:
        print(' 失败：%s' % (x,))

m = call('GET', '/api/v1/rpt/metrics/current')[1].get('data') or {}
print('\n驾驶舱指标：')
for k in ('HOUSE_TOTAL', 'HOUSE_OCCUPIED', 'OCCUPANCY_RATE', 'BILL_UNPAID_AMOUNT',
          'PAYMENT_TOTAL_AMOUNT', 'ACCESS_TODAY_COUNT'):
    print('    %-22s %s' % (k, m.get(k)))
