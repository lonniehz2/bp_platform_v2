# -*- coding: utf-8 -*-
"""开放平台真机验证（需内网：应用 + DB 可达）

覆盖：应用创建/密钥一次性、三道关卡（有效性/访问控制/签名防重放）、
密钥重置、调用日志、用量统计、Webhook 订阅与推送留痕。

用法：python _verify_open.py
"""
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.request

BASE = 'http://192.168.31.11:8080'
TENANT = '350600'
TOK = None
ok = fail = 0


def call(m, p, b=None, token=None, hdr=None):
    h = {'Content-Type': 'application/json', 'X-Tenant-Id': TENANT}
    t = token if token is not None else TOK
    if t:
        h['Authorization'] = 'Bearer ' + t
    if hdr:
        h.update(hdr)
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


def sign(secret, method, path, ts, nonce, body):
    """与 OpenSigner#sign 同口径。"""
    payload = '%s\n%s\n%s\n%s\n%s' % (method.upper(), path, ts, nonce, body or '')
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_sign_call(app_key, secret, api_code, body='', ts=None, nonce=None,
                   path=None):
    ts = str(ts if ts is not None else int(time.time() * 1000))
    nonce = nonce or ('n' + str(int(time.time() * 1000000)))
    path = path or ('/open/' + api_code)
    return {
        'appKey': app_key, 'apiCode': api_code, 'timestamp': ts, 'nonce': nonce,
        'sign': sign(secret, 'POST', path, ts, nonce, body), 'body': body,
    }


print('=' * 78)
print(' 开放平台验证')
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

# ==================== 1. 接口清单（种子）====================
st, r = call('GET', '/api/v1/open/apis')
apis = r.get('data') or []
chk('⭐ 开放接口清单非空（种子 8 个）', len(apis) >= 8, len(apis))
codes = {a.get('apiCode') for a in apis}
chk('含 house.list', 'house.list' in codes, sorted(codes)[:5])

# ==================== 2. 创建应用（密钥仅一次）====================
st, r = call('POST', '/api/v1/open/apps', {
    'appName': '验证应用' + sfx, 'appType': 'THIRD_PARTY',
    'contactName': '张三', 'contactPhone': '13800138000',
    'qpsLimit': 20, 'scopeCodes': '*'})
chk('⭐ 创建开放应用', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
app = r.get('data') or {}
AK = app.get('appKey')
SK = app.get('appSecret')
chk('AppKey 以 AK 开头', str(AK).startswith('AK'), AK)
chk('⭐⭐ 返回明文 AppSecret（仅此一次）', isinstance(SK, str) and len(SK) == 64, SK)
chk('默认状态 ENABLED', app.get('appStatus') == 'ENABLED', app.get('appStatus'))

st, r = call('GET', '/api/v1/open/apps')
lst = r.get('data') or []
chk('应用列表包含新建', any(a.get('appKey') == AK for a in lst), len(lst))
# ⭐ 安全：列表不得回显 secret
leak = [a for a in lst if a.get('appSecret') and a.get('appSecret') == SK]
chk('⭐⭐ 列表不回显明文密钥', not leak, '存在明文泄露')

# ==================== 3. ⭐ 关卡三：签名 ====================
st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call(AK, SK, 'house.list', '{"pageNum":1}'))
chk('⭐⭐ 正确签名通过校验', r.get('code') == 'BP00000',
    str(r.get('code')) + ' ' + str(r.get('message')))
chk('返回租户ID（租户取自应用记录）',
    str((r.get('data') or {}).get('tenantId')) == TENANT,
    (r.get('data') or {}).get('tenantId'))

bad = make_sign_call(AK, SK, 'house.list')
bad['sign'] = 'deadbeef' * 8
st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1', bad)
chk('⭐⭐ 错误签名被拒', r.get('code') == 'BP20001', r.get('code'))

stale = make_sign_call(AK, SK, 'house.list',
                       ts=int(time.time() * 1000) - 6 * 60 * 1000)
st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1', stale)
chk('⭐⭐ 过期时间戳被拒（防重放）', r.get('code') == 'BP20001', r.get('code'))
chk('拒绝信息含“过期”', '过期' in str(r.get('message')), r.get('message'))

tampered = make_sign_call(AK, SK, 'house.list', '{"pageNum":1}')
tampered['body'] = '{"pageNum":2}'
st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1', tampered)
chk('⭐⭐ 篡改 body 签名失效', r.get('code') == 'BP20001', r.get('code'))

st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call('AKNOTEXIST', SK, 'house.list'))
chk('未知 AppKey 被拒', r.get('code') == 'BP20001', r.get('code'))

# ==================== 4. ⭐ 关卡二：授权范围 ====================
st, r = call('POST', '/api/v1/open/apps', {
    'appName': '限权应用' + sfx, 'appType': 'THIRD_PARTY',
    'scopeCodes': 'house.list'})
app2 = r.get('data') or {}
AK2, SK2 = app2.get('appKey'), app2.get('appSecret')
chk('创建限权应用（仅 house.list）', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call(AK2, SK2, 'house.list'))
chk('⭐ 授权范围内接口可调', r.get('code') == 'BP00000', r.get('code'))

st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call(AK2, SK2, 'contract.list'))
chk('⭐⭐ 未授权接口被拒', r.get('code') == 'BP20002', r.get('code'))
chk('拒绝信息含接口名', 'contract.list' in str(r.get('message')), r.get('message'))

# ==================== 5. ⭐ 关卡二：IP 白名单 ====================
st, r = call('POST', '/api/v1/open/apps', {
    'appName': '白名单应用' + sfx, 'appType': 'INTERNAL',
    'ipWhitelist': '10.0.0.9', 'scopeCodes': '*'})
app3 = r.get('data') or {}
AK3, SK3 = app3.get('appKey'), app3.get('appSecret')

st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call(AK3, SK3, 'house.list'))
chk('⭐⭐ 不在白名单的 IP 被拒', r.get('code') == 'BP20002', r.get('code'))

st, r = call('POST', '/api/v1/open/verify?clientIp=10.0.0.9',
             make_sign_call(AK3, SK3, 'house.list'))
chk('⭐ 白名单内 IP 通过', r.get('code') == 'BP00000', r.get('code'))

# ==================== 6. 关卡一：停用 / 过期 ====================
app_id = app.get('id')
st, r = call('POST', '/api/v1/open/apps/%s/status' % app_id,
             {'status': 'DISABLED'})
chk('停用应用', r.get('code') == 'BP00000', r.get('code'))
st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call(AK, SK, 'house.list'))
chk('⭐⭐ 停用后调用被拒', r.get('code') == 'BP20002', r.get('code'))
call('POST', '/api/v1/open/apps/%s/status' % app_id, {'status': 'ENABLED'})

yesterday = time.strftime('%Y-%m-%d', time.localtime(time.time() - 86400))
st, r = call('POST', '/api/v1/open/apps', {
    'appName': '过期应用' + sfx, 'appType': 'THIRD_PARTY',
    'expireDate': yesterday, 'scopeCodes': '*'})
app4 = r.get('data') or {}
st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call(app4.get('appKey'), app4.get('appSecret'), 'house.list'))
chk('⭐⭐ 已过期应用被拒', r.get('code') == 'BP20002', r.get('code'))

# ==================== 7. ⭐ 密钥重置 ====================
st, r = call('POST', '/api/v1/open/apps/%s/reset-secret' % app_id)
newsk = (r.get('data') or {}).get('appSecret')
chk('⭐ 重置密钥返回新密钥', r.get('code') == 'BP00000' and newsk and newsk != SK,
    r.get('code'))
st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call(AK, SK, 'house.list'))
chk('⭐⭐ 旧密钥立即失效', r.get('code') == 'BP20001', r.get('code'))
st, r = call('POST', '/api/v1/open/verify?clientIp=127.0.0.1',
             make_sign_call(AK, newsk, 'house.list'))
chk('⭐ 新密钥可用', r.get('code') == 'BP00000', r.get('code'))
SK = newsk

# ==================== 8. 调用日志 ====================
st, r = call('GET', '/api/v1/open/call-logs?pageNum=1&pageSize=50&appKey=%s' % AK)
logs = (r.get('data') or {}).get('rows') or []
chk('⭐ 调用日志已记录', len(logs) >= 1, len(logs))
if logs:
    chk('日志含耗时', logs[0].get('durationMs') is not None, logs[0].get('durationMs'))
    succ = [x for x in logs if x.get('successFlag') in (1, True, '1')]
    chk('⭐ 同时记录成功与失败', len(succ) >= 1 and len(succ) < len(logs),
        'success=%d total=%d' % (len(succ), len(logs)))
    print('     最近日志：%s → %s（成功 %s，%s ms）'
          % (logs[0].get('apiCode'), logs[0].get('responseCode'),
             logs[0].get('successFlag'), logs[0].get('durationMs')))

st, r = call('GET', '/api/v1/open/usage?appKey=%s' % AK)
u = r.get('data') or {}
chk('⭐ 用量统计', r.get('code') == 'BP00000' and int(u.get('total') or 0) >= 1, u)
print('     用量：总 %s，成功 %s，成功率 %s%%'
      % (u.get('total'), u.get('success'), u.get('successRate')))

# ==================== 9. Webhook ====================
st, r = call('POST', '/api/v1/open/webhooks', {
    'hookName': '非法地址', 'callbackUrl': 'ftp://x', 'eventTypes': 'contract.*'})
chk('⭐ 非 http 回调地址被拒', r.get('code') == 'BP10001', r.get('code'))

st, r = call('POST', '/api/v1/open/webhooks', {
    'hookName': '验证订阅' + sfx, 'eventTypes': 'contract.*,alert.raised',
    'callbackUrl': 'http://127.0.0.1:9/nohook', 'timeoutMs': 500})
chk('⭐ 订阅 Webhook', r.get('code') == 'BP00000', r.get('code'))
hook = r.get('data') or {}
chk('返回签名密钥', bool(hook.get('secretKey')), hook.get('secretKey'))

st, r = call('POST', '/api/v1/open/webhooks/publish', {
    'eventType': 'contract.effective', 'payload': {'contractId': 2001}})
chk('⭐ 发布事件（前缀订阅命中）', r.get('code') == 'BP00000', r.get('code'))
print('     推送成功数：%s（无真实接收方时应为 0）' % r.get('data'))

time.sleep(1)
st, r = call('GET', '/api/v1/open/webhook-logs?pageNum=1&pageSize=10')
wlogs = (r.get('data') or {}).get('rows') or []
chk('⭐⭐ 推送失败仍留痕（不影响主业务）', len(wlogs) >= 1, len(wlogs))
if wlogs:
    print('     推送日志：%s → %s（HTTP %s）'
          % (wlogs[0].get('eventType'), wlogs[0].get('pushStatus'),
             wlogs[0].get('httpStatus')))

st, r = call('POST', '/api/v1/open/webhooks/%s/status' % hook.get('id'),
             {'status': 'DISABLED'})
chk('停用 Webhook', r.get('code') == 'BP00000', r.get('code'))

# ==================== 10. 权限 ====================
st, r = call('POST', '/api/v1/auth/login',
             {'tenantId': TENANT, 'username': 'acceptor', 'password': 'acc123'})
acc = (r.get('data') or {}).get('token')
st, r = call('GET', '/api/v1/open/apps', token=acc)
chk('⭐ 无 open:app:list 权限 → 403', st == 403, st)
st, r = call('POST', '/api/v1/open/apps', {'appName': 'x'}, token=acc)
chk('⭐ 无 open:app:manage 权限 → 403', st == 403, st)

print()
print('-' * 78)
print('  通过 %d / 失败 %d' % (ok, fail))
print('-' * 78)
sys.exit(0 if fail == 0 else 1)
