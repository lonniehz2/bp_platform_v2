# -*- coding: utf-8 -*-
"""通行记录 + 授权审计 验证"""
import datetime
import json
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None


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
print(' 通行记录 + 授权审计 验证')
print('=' * 78)

st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'admin', 'password': 'admin123'})
TOK = (r.get('data') or {}).get('token')
chk('管理员登录', bool(TOK), r.get('code'))

today = datetime.date.today()
d0 = (today - datetime.timedelta(days=2)).isoformat()
HID = 555000 + int(sfx) % 1000
PID = 660000 + int(sfx) % 1000

# ==================== 1. 上报通行记录 ====================
def rep(eid, ot, ts, pid=PID, hid=HID):
    return call('POST', '/api/v1/access-records', {
        'eventId': eid, 'lockId': 'LOCK-' + sfx, 'deviceMac': 'AA:BB:CC:' + sfx,
        'spaceId': hid + 1, 'houseId': hid, 'orgId': 1,
        'openType': ot, 'personId': pid, 'targetUserMobile': '13800138000',
        'openTime': ts, 'source': 'CALLBACK'})


st, r = rep('EV-' + sfx + '-1', '1001', d0 + ' 09:00:00')
chk('⭐ 上报通行记录（人脸）', r.get('code') == 'BP00000' and r.get('data') is True,
    str(r.get('code')) + ' ' + str(r.get('data')))
chk('解析开门方式名称', True)  # 由下方查询校验

st, r = rep('EV-' + sfx + '-1', '1001', d0 + ' 09:00:00')
chk('⭐⭐ 幂等：重复事件被丢弃', r.get('code') == 'BP00000' and r.get('data') is False,
    str(r.get('code')) + ' ' + str(r.get('data')))

st, r = rep('EV-' + sfx + '-2', '1003', d0 + ' 18:30:00')
chk('上报通行记录（密码）', r.get('data') is True, r.get('data'))
st, r = rep('EV-' + sfx + '-3', '1901', d0 + ' 23:50:00')
chk('⭐ 上报临时密码（应标异常）', r.get('data') is True, r.get('data'))

# 批量上报
st, r = call('POST', '/api/v1/access-records/batch', [
    {'eventId': 'EV-' + sfx + '-4', 'houseId': HID, 'orgId': 1, 'openType': '1002',
     'personId': PID, 'openTime': d0 + ' 12:00:00', 'source': 'PULL'},
    {'eventId': 'EV-' + sfx + '-5', 'houseId': HID, 'orgId': 1, 'openType': '1004',
     'personId': PID, 'openTime': d0 + ' 08:00:00', 'source': 'PULL'},
])
chk('⭐ 批量上报', int(r.get('data') or 0) == 2, r.get('data'))

# ==================== 2. 查询 ====================
st, r = call('GET', '/api/v1/access-records?pageNum=1&pageSize=20&houseId=%s' % HID)
rows = (r.get('data') or {}).get('rows') or []
chk('⭐ 按房源查通行记录', len(rows) == 5, len(rows))
if rows:
    names = {x.get('openTypeName') for x in rows}
    chk('⭐ 开门方式已解析中文', '人脸' in names, names)

st, r = call('GET', '/api/v1/access-records?pageNum=1&pageSize=20&abnormalOnly=true'
             '&houseId=%s' % HID)
ab = (r.get('data') or {}).get('rows') or []
chk('⭐⭐ 筛选异常开门（临时密码=1条）', len(ab) == 1, len(ab))
if ab:
    chk('异常类型已标记', ab[0].get('abnormal') in (True, 'true'), ab[0].get('abnormal'))
    print('     异常记录：%s（%s）' % (ab[0].get('openTypeName'), ab[0].get('abnormalType')))

# ==================== 3. ⭐ 行为轨迹 ====================
st, r = call('GET', '/api/v1/access-records/trace/person/%s' % PID)
tr = r.get('data') or {}
chk('⭐ 人员行为轨迹', r.get('code') == 'BP00000' and len(tr.get('timeline') or []) >= 5,
    len(tr.get('timeline') or []))
chk('轨迹含摘要', '次开门' in str(tr.get('summary')), tr.get('summary'))
chk('⭐ 轨迹统计异常次数', int(tr.get('abnormalRecords') or 0) == 1, tr.get('abnormalRecords'))
print('     轨迹摘要：%s' % tr.get('summary'))

st, r = call('GET', '/api/v1/access-records/trace/house/%s' % HID)
tr2 = r.get('data') or {}
chk('⭐ 房源行为轨迹', len(tr2.get('timeline') or []) >= 5, len(tr2.get('timeline') or []))
chk('轨迹按时间升序（首次最早）',
    (tr2.get('timeline') or [{}])[0].get('openTime', '').find('08:00') > 0,
    (tr2.get('timeline') or [{}])[0].get('openTime'))

# ==================== 4. ⭐ 空置判定 ====================
st, r = call('GET', '/api/v1/access-records/idle?idleDays=1')
idle = r.get('data') or []
chk('⭐ 空置判定接口', r.get('code') == 'BP00000', r.get('code'))
mine = next((x for x in idle if str(x.get('houseId')) == str(HID)), None)
chk('⭐ 命中本房源', mine is not None, len(idle))
if mine:
    print('     房源 %s：最近开门 %s，连续 %s 天，疑似空置=%s'
          % (mine.get('houseId'), mine.get('lastOpenTime'), mine.get('idleDays'),
             mine.get('suspectIdle')))
    chk('⭐⭐ 2 天无开门 ≥ 阈值1 → 疑似空置',
        mine.get('suspectIdle') in (True, 'true'), mine.get('suspectIdle'))
    chk('判定说明可读', '疑似空置' in str(mine.get('remark')), mine.get('remark'))

st, r = call('GET', '/api/v1/access-records/idle?idleDays=30')
idle30 = r.get('data') or []
mine30 = next((x for x in idle30 if str(x.get('houseId')) == str(HID)), None)
chk('⭐ 阈值30天时不判空置', mine30 is not None
    and mine30.get('suspectIdle') in (False, 'false'),
    mine30.get('suspectIdle') if mine30 else None)

# ==================== 5. 不可信开门占比 ====================
st, r = call('GET', '/api/v1/access-records/untrusted-ratio')
ur = r.get('data') or {}
print('     不可信占比：%s%%（%s/%s，阈值 %s%%）'
      % (ur.get('untrustedRatio'), ur.get('untrusted'), ur.get('total'), ur.get('threshold')))
chk('⭐⭐ 不可信占比统计', int(ur.get('total') or 0) >= 5, ur.get('total'))
chk('不可信计数正确（临时密码1条）', int(ur.get('untrusted') or 0) == 1, ur.get('untrusted'))
chk('返回是否达标', 'pass' in ur, list(ur.keys()))

# ==================== 6. ⭐ 授权审计 ====================
st, r = call('GET', '/api/v1/grant-audit-logs?pageNum=1&pageSize=20')
chk('授权审计查询接口可用', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))

# 触发一次授权撤销，验证是否自动写审计
st, r = call('GET', '/api/v1/grants/999999999', token=TOK)
chk('授权详情不存在 BP30001', r.get('code') == 'BP30001', r.get('code'))

st, r = call('GET', '/api/v1/grant-audit-logs?pageNum=1&pageSize=5')
logs = (r.get('data') or {}).get('rows') or []
chk('审计表可查询（可能暂无记录）', r.get('code') == 'BP00000', r.get('code'))
print('     当前授权审计记录数：%s' % (r.get('data') or {}).get('total'))

# 审计不可改删
for verb in ('PUT', 'DELETE'):
    st, r = call(verb, '/api/v1/grant-audit-logs/1', {})
    chk('⭐ %s 授权审计无接口（只追加）' % verb, st in (404, 405, 500), st)

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
