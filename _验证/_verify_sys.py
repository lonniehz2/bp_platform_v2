# -*- coding: utf-8 -*-
"""sys 支撑层验证：审计日志 / 字典 / 参数（含参数真实生效）"""
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'


def call(m, p, b=None, token=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    if token:
        h['Authorization'] = 'Bearer ' + token
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


sfx = str(int(time.time()))[-6:]
print('=' * 78)
print(' 系统支撑层验证 · 审计日志 / 字典 / 参数')
print('=' * 78)

# 登录
st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'})
tok = (r.get('data') or {}).get('token')
chk('管理员登录', bool(tok), r.get('code'))

# ==================== 1. 字典 ====================
st, r = call('GET', '/api/v1/sys/dicts/SECURITY_TYPE', token=tok)
d = r.get('data') or []
chk('⭐ 按类型取字典项', r.get('code') == 'BP00000' and len(d) == 4, len(d))
chk('字典项含标签', d[0].get('dictLabel') == '公租房', d[0].get('dictLabel') if d else None)

st, r = call('GET', '/api/v1/sys/dicts/SECURITY_TYPE/map', token=tok)
m = r.get('data') or {}
chk('⭐ 编码→标签映射', m.get('PUBLIC') == '公租房', m)

st, r = call('GET', '/api/v1/sys/dicts', token=tok)
chk('字典类型列表', r.get('code') == 'BP00000' and len(r.get('data') or []) >= 6,
    len(r.get('data') or []))

st, r = call('POST', '/api/v1/sys/dicts', {
    'dictType': 'DEMO_' + sfx, 'dictCode': 'A', 'dictLabel': '演示项A',
    'dictValue': 'A', 'sortNo': 1, 'remark': '演示'}, token=tok)
chk('⭐ 新增字典项', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
dictId = (r.get('data') or {}).get('id')
chk('租户级字典写入', (r.get('data') or {}).get('tenantId') == TENANT,
    (r.get('data') or {}).get('tenantId'))

st, r = call('POST', '/api/v1/sys/dicts', {
    'dictType': 'DEMO_' + sfx, 'dictCode': 'A', 'dictLabel': '重复'}, token=tok)
chk('⭐ 同租户重复字典被拒', r.get('code') == 'BP30002', r.get('code'))

st, r = call('POST', '/api/v1/sys/dicts/%s/status' % dictId, {'enabled': False}, token=tok)
chk('停用字典项', (r.get('data') or {}).get('dictStatus') == 'DISABLED', r.get('code'))
st, r = call('GET', '/api/v1/sys/dicts/DEMO_' + sfx, token=tok)
chk('⭐ 停用后不出现在列表', len(r.get('data') or []) == 0, len(r.get('data') or []))

# ==================== 2. 参数 ====================
st, r = call('GET', '/api/v1/sys/configs', token=tok)
cfgs = r.get('data') or []
chk('⭐ 参数列表', r.get('code') == 'BP00000' and len(cfgs) >= 12, len(cfgs))

st, r = call('GET', '/api/v1/sys/configs/biz.publicity.allocation.minDays', token=tok)
chk('⭐ 读取单个参数 = 7', str(r.get('data')) == '7', r.get('data'))
st, r = call('GET', '/api/v1/sys/configs/biz.credit.banYears.severe', token=tok)
chk('读取禁申年限 = 5', str(r.get('data')) == '5', r.get('data'))
st, r = call('GET', '/api/v1/sys/configs/biz.exchange.noExchange.multiplier', token=tok)
chk('读取应换不换倍率 = 1.5', str(r.get('data')) == '1.5', r.get('data'))

# ==================== 3. ⭐ 参数真实生效（改 7 → 10 天）====================
import datetime
d0 = datetime.date.today()
d6 = (d0 + datetime.timedelta(days=6)).isoformat()

st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': 1, 'title': '参数生效验证-7天',
    'startDate': d0.isoformat(), 'endDate': d6}, token=tok)
chk('⭐ 默认 7 天可创建配租公示', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 改为 10 天
st, r = call('POST', '/api/v1/sys/configs', {
    'key': 'biz.publicity.allocation.minDays', 'value': '10',
    'description': '配租公示最短自然日（临时改为10天验证）'}, token=tok)
chk('⭐ 修改参数为 10', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': 1, 'title': '参数生效验证-7天不再够',
    'startDate': d0.isoformat(), 'endDate': d6}, token=tok)
chk('⭐⭐ 参数生效：7 天现在被拒', r.get('code') == 'BP10001',
    str(r.get('code')) + ' ' + str(r.get('message')))
print('     拒绝信息：%s' % r.get('message'))
chk('拒绝信息含 10', '10' in str(r.get('message')), r.get('message'))

# 恢复
call('POST', '/api/v1/sys/configs', {
    'key': 'biz.publicity.allocation.minDays', 'value': '7',
    'description': '配租公示最短自然日（含首尾）'}, token=tok)
st, r = call('POST', '/api/v1/publicities', {
    'publicityType': 'ALLOCATION', 'orgId': 1, 'title': '参数恢复验证',
    'startDate': d0.isoformat(), 'endDate': d6}, token=tok)
chk('⭐ 恢复为 7 天后可创建', r.get('code') == 'BP00000', r.get('code'))

# ⭐ 换房次数参数生效
st, r = call('POST', '/api/v1/sys/configs', {
    'key': 'biz.exchange.maxTimes', 'value': '2'}, token=tok)
st, r = call('GET', '/api/v1/sys/configs/biz.exchange.maxTimes', token=tok)
chk('⭐ 换房限次参数已更新为 2', str(r.get('data')) == '2', r.get('data'))
call('POST', '/api/v1/sys/configs', {'key': 'biz.exchange.maxTimes', 'value': '1'}, token=tok)

# ==================== 4. ⭐ 审计日志 ====================
st, r = call('GET', '/api/v1/sys/audit-logs?pageNum=1&pageSize=20', token=tok)
logs = (r.get('data') or {}).get('rows') or []
chk('⭐ 审计日志已自动记录', r.get('code') == 'BP00000' and len(logs) >= 1, len(logs))
if logs:
    a = logs[0]
    print('     最近审计：%s / %s / %s / %s'
          % (a.get('auditType'), a.get('auditLevel'), a.get('action'),
             a.get('operatorName')))
    chk('审计含操作人', bool(a.get('operatorName')), a.get('operatorName'))
    chk('审计含动作', bool(a.get('action')), a.get('action'))
    chk('审计含时间', bool(a.get('auditTime')), a.get('auditTime'))
    chk('审计含目标方法', '.' in str(a.get('targetType')), a.get('targetType'))

# 按类型筛选
st, r = call('GET', '/api/v1/sys/audit-logs?pageNum=1&pageSize=20&auditType=DATA', token=tok)
chk('按审计类型筛选', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total', 0)) >= 1,
    (r.get('data') or {}).get('total'))

# 参数修改应产生 CRITICAL 审计
st, r = call('GET', '/api/v1/sys/audit-logs?pageNum=1&pageSize=20&level=CRITICAL', token=tok)
crit = (r.get('data') or {}).get('rows') or []
chk('⭐⭐ 参数修改记为 CRITICAL 级别', len(crit) >= 1, len(crit))
if crit:
    print('     CRITICAL 审计：%s（%s）' % (crit[0].get('action'), crit[0].get('targetType')))
    chk('CRITICAL 审计动作是修改参数', '修改系统参数' in str(crit[0].get('action')),
        crit[0].get('action'))

# 审计不可删改（无接口）
st, r = call('POST', '/api/v1/sys/audit-logs/1', {}, token=tok)
chk('⭐ 审计日志无修改接口', st in (404, 405, 500), st)

# ==================== 5. 权限控制 ====================
st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'acceptor', 'password': 'acc123'})
accTok = (r.get('data') or {}).get('token')
st, r = call('GET', '/api/v1/sys/audit-logs?pageNum=1&pageSize=5', token=accTok)
chk('⭐ 无 sys:audit:list 权限 → 403', st == 403, st)
st, r = call('POST', '/api/v1/sys/configs', {'key': 'x', 'value': '1'}, token=accTok)
chk('⭐ 无 sys:config:edit 权限 → 403', st == 403, st)
st, r = call('GET', '/api/v1/sys/dicts/SECURITY_TYPE', token=accTok)
chk('⭐ 字典查询无需特殊权限（登录即可）', r.get('code') == 'BP00000', r.get('code'))

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
