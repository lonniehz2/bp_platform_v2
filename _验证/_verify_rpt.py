# -*- coding: utf-8 -*-
"""报表 / 大屏 / 指标 验证"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None


def call(m, p, b=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if TOK:
        h['Authorization'] = 'Bearer ' + TOK
    d = json.dumps(b).encode() if b is not None else None
    r = urllib.request.Request(BASE + p, data=d, method=m, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=40) as x:
            raw = x.read().decode('utf-8', 'replace')
            try:
                return x.status, json.loads(raw)
            except Exception:
                return x.status, {'code': 'HTML'}
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {'code': 'HTTP_%d' % e.code}


ok = fail = 0


def chk(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1
        print('  [PASS] ' + name)
    else:
        fail += 1
        print('  [FAIL] ' + name + '  ' + str(extra))


print('=' * 78)
print(' 报表导出 + 可配置大屏 + 指标 验证')
print('=' * 78)

st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'})
TOK = (r.get('data') or {}).get('token')
chk('管理员登录', bool(TOK), r.get('code'))

# ==================== 1. 报表定义与查询 ====================
st, r = call('GET', '/api/v1/rpt/reports')
reps = r.get('data') or []
chk('⭐ 报表定义列表（3 张内置）', len(reps) == 3, len(reps))
codes = {x.get('reportCode') for x in reps}
chk('含房源/合同/欠费台账',
    {'HOUSE_LEDGER', 'CONTRACT_LEDGER', 'ARREARS_LEDGER'} <= codes, codes)

st, r = call('POST', '/api/v1/rpt/reports/query',
             {'reportCode': 'HOUSE_LEDGER', 'pageNum': 1, 'pageSize': 5})
res = r.get('data') or {}
chk('⭐ 房源台账查询', r.get('code') == 'BP00000', r.get('code'))
chk('返回列定义', len(res.get('columns') or []) == 5, len(res.get('columns') or []))
chk('⭐ 中文列标题', (res.get('columns') or [{}])[0].get('title') == '房源编号',
    (res.get('columns') or [{}])[0])
print('     房源台账：total=%s，本页 %s 行'
      % (res.get('total'), len(res.get('rows') or [])))
chk('有数据行', int(res.get('total') or 0) >= 1, res.get('total'))
chk('摘要可读', '共' in str(res.get('summary')), res.get('summary'))

st, r = call('POST', '/api/v1/rpt/reports/query',
             {'reportCode': 'CONTRACT_LEDGER'})
chk('⭐ 合同台账查询', r.get('code') == 'BP00000'
    and len((r.get('data') or {}).get('columns') or []) == 6, r.get('code'))

st, r = call('POST', '/api/v1/rpt/reports/query', {'reportCode': 'NOPE'})
chk('不存在的报表 BP30001', r.get('code') == 'BP30001', r.get('code'))

# ==================== 2. ⭐ 导出 CSV ====================
st, r = call('POST', '/api/v1/rpt/exports?userId=9001',
             {'reportCode': 'HOUSE_LEDGER'})
chk('⭐⭐ 发起导出', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
task = r.get('data') or {}
tid = task.get('id')
chk('任务号 EX 开头', str(task.get('taskNo', '')).startswith('EX'), task.get('taskNo'))
chk('⭐⭐ 导出成功 SUCCESS', task.get('taskStatus') == 'SUCCESS', task.get('taskStatus'))
chk('进度 100', int(task.get('progress') or 0) == 100, task.get('progress'))
chk('⭐ 有文件名', str(task.get('fileName', '')).endswith('.csv'), task.get('fileName'))
chk('文件大小 > 0', int(task.get('fileSize') or 0) > 0, task.get('fileSize'))
chk('导出行数 >= 1', int(task.get('rowCount') or 0) >= 1, task.get('rowCount'))
print('     导出文件：%s（%s 行，%s 字节）'
      % (task.get('fileName'), task.get('rowCount'), task.get('fileSize')))

st, r = call('GET', '/api/v1/rpt/exports/%s/content' % tid)
body = str(r.get('data') or '')
chk('⭐ 可读取导出文件内容', '房源编号' in body, body[:60])
chk('CSV 含数据行', body.count('\n') >= 2, body.count('\n'))
print('     文件首行：%s' % body.split('\n')[0][:80])

st, r = call('GET', '/api/v1/rpt/exports?userId=9001')
chk('⭐ 导出任务列表', r.get('code') == 'BP00000'
    and len(r.get('data') or []) >= 1, len(r.get('data') or []))

# 欠费台账导出
st, r = call('POST', '/api/v1/rpt/exports', {'reportCode': 'ARREARS_LEDGER'})
chk('⭐ 欠费台账导出', (r.get('data') or {}).get('taskStatus') == 'SUCCESS',
    (r.get('data') or {}).get('taskStatus'))

# ==================== 3. ⭐ 可配置大屏 ====================
st, r = call('GET', '/api/v1/rpt/screens')
chk('⭐ 大屏定义列表', r.get('code') == 'BP00000'
    and len(r.get('data') or []) >= 1, len(r.get('data') or []))

st, r = call('GET', '/api/v1/rpt/screens/OVERVIEW/data')
d = r.get('data') or {}
chk('⭐⭐ 大屏数据接口', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
widgets = d.get('widgets') or []
chk('⭐ 按配置返回 8 个组件', len(widgets) == 8, len(widgets))
chk('含刷新间隔', d.get('refreshSeconds') is not None, d.get('refreshSeconds'))
print('     大屏组件：')
for w in widgets:
    print('       %-22s %-10s = %s' % (w.get('title'), w.get('chart'), w.get('value')))
chk('⭐ 组件值非空', all(w.get('value') is not None for w in widgets),
    [w.get('code') for w in widgets if w.get('value') is None])
chk('出租率在 0-100 之间',
    0 <= float(next((w.get('value') for w in widgets
                     if w.get('code') == 'OCCUPANCY_RATE'), 0)) <= 100,
    next((w.get('value') for w in widgets if w.get('code') == 'OCCUPANCY_RATE'), None))

# 自定义大屏（配置驱动验证）
st, r = call('POST', '/api/v1/rpt/screens', {
    'screenCode': 'DEMO' + str(int(time.time()))[-4:],
    'screenName': '自定义大屏', 'screenType': 'OVERVIEW',
    'widgetConfig': '[{"code":"HOUSE_TOTAL","title":"我的房源数","chart":"NUMBER"},'
                    '{"code":"ACCESS_TODAY_COUNT","title":"今日开门","chart":"LINE"}]',
    'refreshSeconds': 30})
chk('⭐ 新建自定义大屏', r.get('code') == 'BP00000', r.get('code'))
code2 = (r.get('data') or {}).get('screenCode')
st, r = call('GET', '/api/v1/rpt/screens/%s/data' % code2)
w2 = (r.get('data') or {}).get('widgets') or []
chk('⭐⭐ 配置驱动：仅返回配置的 2 个组件', len(w2) == 2, len(w2))
chk('自定义标题生效',
    (w2[0] or {}).get('title') == '我的房源数', (w2[0] or {}).get('title'))
chk('刷新间隔 30', int((r.get('data') or {}).get('refreshSeconds') or 0) == 30,
    (r.get('data') or {}).get('refreshSeconds'))

st, r = call('GET', '/api/v1/rpt/screens/NOPE/data')
chk('不存在的大屏 BP30001', r.get('code') == 'BP30001', r.get('code'))

# ==================== 4. 指标 ====================
st, r = call('GET', '/api/v1/rpt/metrics/current')
m = r.get('data') or {}
chk('⭐ 实时指标（9 项）', len(m) >= 9, len(m))
for k in ('HOUSE_TOTAL', 'OCCUPANCY_RATE', 'BILL_UNPAID_AMOUNT'):
    chk('含指标 %s' % k, k in m, list(m.keys())[:6])
print('     指标：房源 %s，出租率 %s%%，欠费金额 %s'
      % (m.get('HOUSE_TOTAL'), m.get('OCCUPANCY_RATE'), m.get('BILL_UNPAID_AMOUNT')))

st, r = call('GET', '/api/v1/rpt/metrics/current/HOUSE_TOTAL')
chk('⭐ 单指标查询', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/rpt/metrics/snapshot')
chk('⭐⭐ 指标日快照', r.get('code') == 'BP00000' and int(r.get('data') or 0) >= 9,
    r.get('data'))
st, r = call('GET', '/api/v1/rpt/metrics/trend/HOUSE_TOTAL')
chk('⭐ 指标趋势查询', r.get('code') == 'BP00000'
    and len(r.get('data') or []) >= 1, len(r.get('data') or []))
if r.get('data'):
    print('     趋势首点：%s = %s'
          % (r.get('data')[0].get('statDate'), r.get('data')[0].get('metricValue')))

# 幂等：同日快照不重复插入
st, r = call('POST', '/api/v1/rpt/metrics/snapshot')
st, r = call('GET', '/api/v1/rpt/metrics/trend/HOUSE_TOTAL')
chk('⭐ 同日快照幂等（仍 1 条）', len(r.get('data') or []) == 1, len(r.get('data') or []))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
