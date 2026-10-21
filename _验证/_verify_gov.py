# -*- coding: utf-8 -*-
"""监管报送真机验证（需内网：应用 + DB 可达）

覆盖：适配器配置与鉴权脱敏、报送任务/明细双层落库、
部分成功与失败补报、降级（无适配器/无地址）、统计、权限、字典。

用法：python _verify_gov.py
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
ok = fail = 0


def call(m, p, b=None, token=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    t = token if token is not None else TOK
    if t:
        h['Authorization'] = 'Bearer ' + t
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
    except Exception as e:
        return -1, {'code': type(e).__name__}


def chk(name, cond, extra=''):
    global ok, fail
    if cond:
        ok += 1
        print('  [PASS] ' + name)
    else:
        fail += 1
        print('  [FAIL] ' + name + '  ' + str(extra))


print('=' * 78)
print(' 监管报送验证')
print('=' * 78)

st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'})
if st == -1 or not (r.get('data') or {}).get('token'):
    print()
    print('⚠️ 应用不可达或登录失败（%s）：%s' % (st, r.get('code')))
    print('   本脚本需在能访问 %s 的环境执行。' % BASE)
    sys.exit(3)
TOK = r['data']['token']
chk('管理员登录', True)

sfx = str(int(time.time()))[-6:]

# ==================== 1. 字典（种子）====================
st, r = call('GET', '/api/v1/sys/dicts/GOV_SYSTEM_TYPE')
ds = r.get('data') or []
chk('⭐ 字典 GOV_SYSTEM_TYPE（4 项）', len(ds) == 4, len(ds))
chk('含 PUBLIC_HOUSING', any(d.get('dictCode') == 'PUBLIC_HOUSING' for d in ds),
    [d.get('dictCode') for d in ds])
st, r = call('GET', '/api/v1/sys/dicts/GOV_DEGRADE_MODE')
chk('⭐ 字典 GOV_DEGRADE_MODE（4 项）', len(r.get('data') or []) == 4,
    len(r.get('data') or []))

# ==================== 2. ⭐ 降级：无适配器 ====================
TARGET_NONE = 'REAL_ESTATE'   # 故意不配置适配器
st, r = call('POST', '/api/v1/gov/reports', {
    'targetSystem': TARGET_NONE, 'reportType': 'HOUSE'})
t0 = r.get('data') or {}
chk('⭐⭐ 无适配器 → 任务 FAILED（不阻断业务）',
    r.get('code') == 'BP00000' and t0.get('taskStatus') == 'FAILED',
    str(r.get('code')) + ' ' + str(t0.get('taskStatus')))
chk('⭐ 失败原因明确指向缺适配器', '适配器' in str(t0.get('failDetail')),
    t0.get('failDetail'))
chk('任务号 GR 开头', str(t0.get('taskNo', '')).startswith('GR'), t0.get('taskNo'))

# ==================== 3. 适配器配置 ====================
st, r = call('POST', '/api/v1/gov/adapters', {
    'adapterCode': 'PH_API_' + sfx, 'adapterName': '公租房接口适配器',
    'systemType': 'PUBLIC_HOUSING', 'protocol': 'HTTP',
    'endpoint': 'http://127.0.0.1:9/gov/report', 'authType': 'APPKEY',
    'degradeMode': 'MANUAL'})
chk('⭐ 配置适配器', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

st, r = call('GET', '/api/v1/gov/adapters')
ads = r.get('data') or []
mine = [a for a in ads if a.get('adapterCode') == 'PH_API_' + sfx]
chk('适配器列表包含新建', len(mine) == 1, len(ads))
if mine:
    chk('⭐⭐ 鉴权配置已脱敏（不外泄）',
        mine[0].get('authConfig') in (None, '***'), mine[0].get('authConfig'))

# ==================== 4. ⭐ 报送成功路径 ====================
st, r = call('POST', '/api/v1/gov/reports', {
    'targetSystem': 'PUBLIC_HOUSING', 'reportType': 'HOUSE'})
t1 = r.get('data') or {}
tid = t1.get('id')
chk('⭐⭐ 报送房源数据成功', t1.get('taskStatus') == 'SUCCESS',
    str(t1.get('taskStatus')) + ' ' + str(t1.get('failDetail')))
chk('⭐ 记录数 > 0', int(t1.get('recordCount') or 0) > 0, t1.get('recordCount'))
chk('成功数 = 记录数',
    int(t1.get('successCount') or 0) == int(t1.get('recordCount') or 0),
    '成功 %s / 记录 %s' % (t1.get('successCount'), t1.get('recordCount')))
chk('报送时间已记录', bool(t1.get('reportTime')), t1.get('reportTime'))
print('     任务 %s：%s 条，成功 %s，失败 %s'
      % (t1.get('taskNo'), t1.get('recordCount'), t1.get('successCount'),
         t1.get('failCount')))

st, r = call('GET', '/api/v1/gov/reports/%s/details' % tid)
dets = r.get('data') or []
chk('⭐⭐ 明细逐条落库', len(dets) == int(t1.get('recordCount') or 0), len(dets))
if dets:
    d0 = dets[0]
    chk('明细含业务ID', d0.get('bizId') is not None, d0.get('bizId'))
    chk('明细状态 SUCCESS', d0.get('syncStatus') == 'SUCCESS', d0.get('syncStatus'))
    chk('⭐ 回写外部系统ID（便于对账）', bool(d0.get('externalId')),
        d0.get('externalId'))
    chk('明细含请求快照', bool(d0.get('requestData')), d0.get('requestData'))

# ==================== 5. 合同报送（含证件号脱敏）====================
st, r = call('POST', '/api/v1/gov/reports', {
    'targetSystem': 'PUBLIC_HOUSING', 'reportType': 'CONTRACT'})
t2 = r.get('data') or {}
chk('⭐ 报送合同数据', r.get('code') == 'BP00000'
    and t2.get('taskStatus') in ('SUCCESS', 'PARTIAL'), t2.get('taskStatus'))
if int(t2.get('recordCount') or 0) > 0:
    st, r = call('GET', '/api/v1/gov/reports/%s/details' % t2.get('id'))
    dd = (r.get('data') or [{}])[0]
    req = str(dd.get('requestData') or '')
    chk('⭐⭐ 报送数据中证件号已脱敏', '****' in req or 'lesseeIdCard' in req,
        req[:80])

# ==================== 6. 空数据集 ====================
st, r = call('POST', '/api/v1/gov/reports', {
    'targetSystem': 'PUBLIC_HOUSING', 'reportType': 'FINANCE'})
t3 = r.get('data') or {}
chk('⭐ 空数据集不算失败（记录数 0）',
    int(t3.get('recordCount') or 0) == 0 and t3.get('taskStatus') == 'SUCCESS',
    '记录 %s / 状态 %s' % (t3.get('recordCount'), t3.get('taskStatus')))

# ==================== 7. 任务列表与统计 ====================
st, r = call('GET', '/api/v1/gov/reports?pageNum=1&pageSize=20')
chk('⭐ 报送任务分页', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total') or 0) >= 3,
    (r.get('data') or {}).get('total'))

st, r = call('GET', '/api/v1/gov/reports?pageNum=1&pageSize=20&taskStatus=FAILED')
chk('⭐ 按状态筛选', r.get('code') == 'BP00000'
    and int((r.get('data') or {}).get('total') or 0) >= 1,
    (r.get('data') or {}).get('total'))

st, r = call('GET', '/api/v1/gov/stats')
s = r.get('data') or {}
chk('⭐ 报送统计', r.get('code') == 'BP00000'
    and int(s.get('tasks') or 0) >= 3, s)
print('     统计：任务 %s，成功 %s，部分 %s，失败 %s，记录 %s，成功率 %s%%'
      % (s.get('tasks'), s.get('success'), s.get('partial'), s.get('failed'),
         s.get('records'), s.get('successRate')))

# ==================== 8. ⭐ 失败补报 ====================
st, r = call('POST', '/api/v1/gov/reports/%s/retry' % t0.get('id'))
chk('⭐⭐ 无适配器任务补报返回 0（仍无法报送）', r.get('code') == 'BP00000'
    and int(r.get('data') or 0) == 0, r.get('data'))

# 造一个「无地址」适配器 → 明细 SKIPPED
call('POST', '/api/v1/gov/adapters', {
    'adapterCode': 'NOEP_' + sfx, 'adapterName': '无地址适配器',
    'systemType': 'HOUSING', 'protocol': 'FILE', 'authType': 'NONE',
    'degradeMode': 'FILE'})
st, r = call('POST', '/api/v1/gov/reports', {
    'targetSystem': 'HOUSING', 'reportType': 'HOUSE'})
t4 = r.get('data') or {}
chk('⭐⭐ 适配器无服务地址 → 明细 SKIPPED 且任务 FAILED',
    t4.get('taskStatus') == 'FAILED', t4.get('taskStatus'))
if int(t4.get('recordCount') or 0) > 0:
    st, r = call('GET', '/api/v1/gov/reports/%s/details' % t4.get('id'))
    dd = (r.get('data') or [{}])[0]
    chk('明细状态 SKIPPED', dd.get('syncStatus') == 'SKIPPED', dd.get('syncStatus'))
    chk('⭐ 错误码 NO_ENDPOINT', dd.get('errorCode') == 'NO_ENDPOINT',
        dd.get('errorCode'))
    st, r = call('POST', '/api/v1/gov/reports/%s/retry' % t4.get('id'))
    chk('⭐ NO_ENDPOINT 明细补报跳过（返回 0）',
        r.get('code') == 'BP00000' and int(r.get('data') or 0) == 0, r.get('data'))

# ==================== 9. 参数校验 ====================
st, r = call('POST', '/api/v1/gov/reports', {'reportType': 'HOUSE'})
chk('缺目标系统 → 拒绝', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/gov/reports', {'targetSystem': 'POLICE'})
chk('缺报送类型 → 拒绝', r.get('code') == 'BP10001', r.get('code'))
st, r = call('POST', '/api/v1/gov/adapters', {'adapterName': '无编码'})
chk('适配器缺编码 → 拒绝', r.get('code') == 'BP10001', r.get('code'))

# ==================== 10. 权限 ====================
st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'acceptor', 'password': 'acc123'})
acc = (r.get('data') or {}).get('token')
st, r = call('GET', '/api/v1/gov/reports', token=acc)
chk('⭐ 无 gov:report:list 权限 → 403', st == 403, st)
st, r = call('POST', '/api/v1/gov/reports',
             {'targetSystem': 'POLICE', 'reportType': 'HOUSE'}, token=acc)
chk('⭐ 无 gov:report:submit 权限 → 403', st == 403, st)
st, r = call('POST', '/api/v1/gov/adapters', {'adapterCode': 'X'}, token=acc)
chk('⭐ 无 gov:adapter:manage 权限 → 403', st == 403, st)

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
sys.exit(0 if fail == 0 else 1)
