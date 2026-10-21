# -*- coding: utf-8 -*-
"""确定哪些参数需要 AES 加密（黑盒枚举）"""
import base64
import hashlib
import itertools
import json
import ssl
import time
import urllib.error
import urllib.request

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

APP_KEY = '4576A20261019122812842505'
APP_SECRET = '1D42A794106300F54B55627F55400A89'
AGENT_CODE = '20261019001'
BASE = 'https://api.hzbit.cn:4443'
TOKEN_PATH = '/ymd/auth-service/sys/getAccessToken'
LOCKS_PATH = '/ymd/lockPt-service/pt/getPtAgentLocks'

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def md5u(s):
    return hashlib.md5(s.encode()).hexdigest().upper()


def sign_of(p):
    return md5u('&'.join('%s=%s' % (k, p[k]) for k in sorted(p)))


def post(path, payload, timeout=25):
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=body, method='POST',
                                 headers={'Content-Type': 'application/json;charset=UTF-8'})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:
        return -1, str(e)


# token
p = {'appKey': APP_KEY, 'appSecret': APP_SECRET, 'time': str(int(time.time())), 'version': '1.0.0'}
p['sign'] = sign_of(p)
_, r = post(TOKEN_PATH, p)
token = json.loads(r)['data']['token']
key = token[:16].encode()


def enc(v):
    return base64.b64encode(AES.new(key, AES.MODE_ECB).encrypt(pad(str(v).encode(), 16))).decode()


print('token[:16] = %r' % token[:16])
print('加密示例 agentCode -> %s' % enc(AGENT_CODE))
print()

# 组合：(agentCode加密, appKey加密, appSecret加密)
combos = [
    ('全部加密', True, True, True),
    ('appKey明文/appSecret密', True, False, True),
    ('appKey密/appSecret明文', True, True, False),
    ('appKey/appSecret均明文', True, False, False),
    ('无appKey/appSecret', True, None, None),
]

for label, ea, ek, es in combos:
    payload = {
        'agentCode': enc(AGENT_CODE) if ea else AGENT_CODE,
        'time': str(int(time.time())),
        'token': token,
        'version': '1.0.0',
    }
    if ek is not None:
        payload['appKey'] = enc(APP_KEY) if ek else APP_KEY
    if es is not None:
        payload['appSecret'] = enc(APP_SECRET) if es else APP_SECRET
    payload['sign'] = sign_of(payload)

    status, resp = post(LOCKS_PATH, payload)
    print('--- %s' % label)
    print('    响应: %s' % resp[:500])

    try:
        j = json.loads(resp)
        if str(j.get('status')) == '1':
            print('\n    ★★★ 成功 ★★★')
            d = j.get('data')
            if isinstance(d, list):
                print('    门锁数: %d' % len(d))
                if d:
                    print('    首条: %s' % json.dumps(d[0], ensure_ascii=False)[:600])
            elif isinstance(d, dict):
                print('    data: %s' % json.dumps(d, ensure_ascii=False)[:600])
            break
    except Exception:
        pass
    print()
    time.sleep(0.5)
