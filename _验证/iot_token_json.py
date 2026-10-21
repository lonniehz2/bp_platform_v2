# -*- coding: utf-8 -*-
"""
IoT 鉴权（修正版）：Content-Type = application/json
MD5 算法已用文档示例验证正确（PASS）
"""
import hashlib
import json
import ssl
import time
import urllib.error
import urllib.request

APP_KEY = '4576A20261019122812842505'
APP_SECRET = '1D42A794106300F54B55627F55400A89'
BASE = 'https://api.hzbit.cn:4443'
TOKEN_PATH = '/ymd/auth-service/sys/getAccessToken'


def md5_upper(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest().upper()


def sign_of(params):
    return md5_upper('&'.join('%s=%s' % (k, params[k]) for k in sorted(params.keys())))


def post_json(path, params, timeout=20):
    body = json.dumps(params, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        BASE + path, data=body, method='POST',
        headers={'Content-Type': 'application/json;charset=UTF-8',
                 'Accept': 'application/json'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return -1, str(e)


def try_variant(label, extra, time_unit='s'):
    ts = str(int(time.time())) if time_unit == 's' else str(int(time.time() * 1000))
    base_params = {'appKey': APP_KEY, 'time': ts, 'version': '1.0.0'}
    base_params.update(extra)

    sign = sign_of(base_params)
    payload = dict(base_params)
    payload['sign'] = sign

    print('\n--- %s' % label)
    print('    sign串: %s' % '&'.join('%s=%s' % (k, base_params[k]) for k in sorted(base_params)))
    print('    sign  : %s' % sign)
    status, resp = post_json(TOKEN_PATH, payload)
    print('    HTTP %d  %s' % (status, resp[:500]))
    return status, resp


print('=' * 72)
print(' IoT getAccessToken（JSON 方式）')
print('=' * 72)

variants = [
    ('A. 含 appSecret，time=秒', {'appSecret': APP_SECRET}, 's'),
    ('B. 不含 appSecret，time=秒', {}, 's'),
    ('C. 含 appSecret，time=毫秒', {'appSecret': APP_SECRET}, 'ms'),
]

success = False
for label, extra, unit in variants:
    st, resp = try_variant(label, extra, unit)
    low = resp.lower().replace(' ', '')
    if '"token"' in low or ("'token'" in low) or ('accesstoken' in low):
        print('\n>>> ✅ 成功：%s' % label)
        print('    响应: %s' % resp[:800])
        success = True
        break
    time.sleep(1)

if not success:
    print('\n>>> 三种组合均未取得 token，需继续排查（见上方错误码）')
