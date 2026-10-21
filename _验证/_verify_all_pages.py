# -*- coding: utf-8 -*-
"""全功能页面对照检查：逐页调用接口，验证有数据、无报错"""
import json
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None

# (页面名, 方法, 路径, 期望 total>0 或 数据非空)
PAGES = [
    ('运营驾驶舱', 'GET', '/api/v1/rpt/screens/OVERVIEW/data', True),
    ('指标接口', 'GET', '/api/v1/rpt/metrics/current', True),
    ('组织机构', 'GET', '/api/v1/orgs?pageNum=1&pageSize=20', True),
    ('空间层级', 'GET', '/api/v1/spaces/tree?orgId=370832680775979008', True),
    ('房源台账', 'GET', '/api/v1/houses?pageNum=1&pageSize=20', True),
    ('人员档案', 'GET', '/api/v1/persons?pageNum=1&pageSize=20', True),
    ('保障档案', 'GET', '/api/v1/guarantee-profiles?pageNum=1&pageSize=20', True),
    ('实名认证', 'GET', '/api/v1/verify-records?pageNum=1&pageSize=20', True),
    ('申请与审核', 'GET', '/api/v1/applications?pageNum=1&pageSize=20', True),
    ('公示管理', 'GET', '/api/v1/publicities?pageNum=1&pageSize=20', True),
    ('轮候管理', 'GET', '/api/v1/allocation/waiting?pageNum=1&pageSize=20', True),
    ('配租与摇号', 'GET', '/api/v1/allocation/batches?pageNum=1&pageSize=20', True),
    ('配租单', 'GET', '/api/v1/allocation/allocations?pageNum=1&pageSize=20', True),
    ('合同管理', 'GET', '/api/v1/contracts?pageNum=1&pageSize=20', True),
    ('合同变更', 'GET', '/api/v1/contract-changes?pageNum=1&pageSize=20', False),
    ('年审复核', 'GET', '/api/v1/annual-reviews?pageNum=1&pageSize=20', True),
    ('退租管理', 'GET', '/api/v1/terminations?pageNum=1&pageSize=20', False),
    ('账单与缴费', 'GET', '/api/v1/fin/bills?pageNum=1&pageSize=20', True),
    ('收款单', 'GET', '/api/v1/fin/payments?pageNum=1&pageSize=20', True),
    ('押金与退款', 'GET', '/api/v1/fin/deposits?pageNum=1&pageSize=20', True),
    ('退款单', 'GET', '/api/v1/fin/refunds?pageNum=1&pageSize=20', True),
    ('补贴管理', 'GET', '/api/v1/fin/subsidies/records?pageNum=1&pageSize=20', True),
    ('计费项目', 'GET', '/api/v1/fin/fee-items?pageNum=1&pageSize=20', True),
    ('催缴管理', 'GET', '/api/v1/fin/dunnings?pageNum=1&pageSize=20', True),
    ('资金流水', 'GET', '/api/v1/fin/cash-flows?pageNum=1&pageSize=20', True),
    ('财务对账', 'GET', '/api/v1/fin/reconciles?pageNum=1&pageSize=20', False),
    ('工单维保', 'GET', '/api/v1/workorders?pageNum=1&pageSize=20', False),
    ('告警与规则', 'GET', '/api/v1/alerts?pageNum=1&pageSize=20', False),
    ('规则集', 'GET', '/api/v1/rules/rulesets', False),
    ('设备管理', 'GET', '/api/v1/devices?pageNum=1&pageSize=20', False),
    ('通行记录', 'GET', '/api/v1/access-records?pageNum=1&pageSize=20', True),
    ('消息待办', 'GET', '/api/v1/messages/todos?pageNum=1&pageSize=20', False),
    ('报表导出', 'GET', '/api/v1/rpt/reports', True),
    ('大屏定义', 'GET', '/api/v1/rpt/screens', True),
    ('钥匙包', 'GET', '/api/v1/keyring?pageNum=1&pageSize=20', False),
    ('授权与对账', 'GET', '/api/v1/grants?pageNum=1&pageSize=20', False),
    ('对账差异', 'GET', '/api/v1/grant-reconcile/diffs?pageNum=1&pageSize=20', False),
    ('用户与权限', 'GET', '/api/v1/rbac/users?pageNum=1&pageSize=20', True),
    ('系统支撑-审计', 'GET', '/api/v1/sys/audit-logs?pageNum=1&pageSize=20', True),
    ('系统支撑-字典', 'GET', '/api/v1/sys/dicts/HOUSE_TYPE', True),
    ('系统支撑-参数', 'GET', '/api/v1/sys/configs', False),
    ('开放平台', 'GET', '/api/v1/open/apps', False),
    ('开放接口清单', 'GET', '/api/v1/open/apis', True),
    ('监管报送', 'GET', '/api/v1/gov/reports?pageNum=1&pageSize=20', False),
    ('政务适配器', 'GET', '/api/v1/gov/adapters', False),
    ('短租订单', 'GET', '/api/v1/short-rent-orders?pageNum=1&pageSize=20', False),
]


def call(m, p):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    r = urllib.request.Request(BASE + p, method=m, headers=h)
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


TOK = call('POST', '/api/v1/auth/login')[1] if False else None
r = urllib.request.Request(
    BASE + '/api/v1/auth/login',
    data=json.dumps({'tenantId': TENANT, 'username': 'admin',
                     'password': 'admin123'}).encode(),
    method='POST', headers={'Content-Type': 'application/json'})
TOK = json.loads(urllib.request.urlopen(r, timeout=30).read().decode())['data']['token']

print('=' * 78)
print(' 全功能页面对照检查（%d 项）' % len(PAGES))
print('=' * 78)
good = empty = bad = 0
badlist = []
for name, meth, path, expect_data in PAGES:
    st, body = call(meth, path)
    code = body.get('code')
    d = body.get('data')
    if st != 200 or code != 'BP00000':
        bad += 1
        badlist.append((name, code, str(body.get('message'))[:60]))
        print('  ✗ %-16s %s %s' % (name, code, str(body.get('message'))[:56]))
        continue
    # 判断是否有数据
    n = 0
    if isinstance(d, dict):
        n = int(d.get('total') or len(d.get('rows') or []) or
                len(d.get('widgets') or []) or (1 if d else 0))
    elif isinstance(d, list):
        n = len(d)
    else:
        n = 1 if d else 0
    if n > 0:
        good += 1
        print('  ✓ %-16s %s 条/项' % (name, n))
    else:
        if expect_data:
            empty += 1
            print('  ○ %-16s 接口正常但无数据' % name)
        else:
            good += 1
            print('  ✓ %-16s 空（可接受）' % name)

print()
print('-' * 78)
print(' 有数据 %d ｜ 接口正常但空 %d ｜ 失败 %d' % (good, empty, bad))
if badlist:
    print(' 失败明细：')
    for n, c, m in badlist:
        print('   %-16s %s %s' % (n, c, m))
print('-' * 78)
