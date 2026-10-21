# -*- coding: utf-8 -*-
"""
IoT 鉴权算法校正：用文档示例验证 MD5 实现，再推导正确 sign 规则
文档示例：
  str  = "loginname=t4nU902RvhliiPlMMcrzWw==&logpwd=oFbqQ8bx8KvkHCI/Q2Kaxw==&time=1553595995&version=1.0.0"
  sign = "46812299FB1BC111AC69A27F99068BE2"
"""
import hashlib
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

APP_KEY = '4576A20261019122812842505'
APP_SECRET = '1D42A794106300F54B55627F55400A89'
BASE = 'https://api.hzbit.cn:4443'
TOKEN_PATH = '/ymd/auth-service/sys/getAccessToken'


def md5_upper(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest().upper()


def md5_lower(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest().lower()


# ---------- 1) 用文档示例验证 MD5 实现 ----------
DOC_STR = ('loginname=t4nU902RvhliiPlMMcrzWw=='
           '&logpwd=oFbqQ8bx8KvkHCI/Q2Kaxw=='
           '&time=1553595995'
           '&version=1.0.0')
DOC_SIGN = '46812299FB1BC111AC69A27F99068BE2'

print('=== 1. 用文档示例校验 MD5 实现 ===')
print('  待验串 : %s' % DOC_STR)
print('  期望值 : %s' % DOC_SIGN)
print('  MD5大写: %s   %s' % (md5_upper(DOC_STR),
                              'PASS' if md5_upper(DOC_STR) == DOC_SIGN else 'FAIL'))
print('  MD5小写: %s' % md5_lower(DOC_STR))
ok_md5 = md5_upper(DOC_STR) == DOC_SIGN
if not ok_md5:
    print('  → MD5 实现与文档不一致，后续结论需谨慎')

# ---------- 2) 尝试多种 sign 组合 ----------
def try_token(label, params, timeout=20):
    sign = md5_upper('&'.join('%s=%s' % (k, params[k]) for k in sorted(params.keys())))
    p = dict(params)
    p['sign'] = sign
    print('\n--- %s' % label)
    print('    sign串: %s' % '&'.join('%s=%s' % (k, sorted(params)[i] and params[k])
                                      for i, k in enumerate(sorted(params))))
    body = urllib.parse.urlencode(p).encode('utf-8')
    req = urllib.request.Request(
        BASE + TOKEN_PATH, data=body, method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                 'Accept': 'application/json'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            raw = r.read().decode('utf-8', 'replace')
            print('    HTTP %d  %s' % (r.status, raw[:400]))
            return raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode('utf-8', 'replace')
        print('    HTTP %d  %s' % (e.code, raw[:400]))
        return raw
    except Exception as e:
        print('    失败: %s' % e)
        return None


print('\n=== 2. 尝试不同参数组合（time 用秒）===')
ts_sec = str(int(time.time()))

variants = [
    ('A. 含 appSecret，time=秒',
     {'appKey': APP_KEY, 'appSecret': APP_SECRET, 'time': ts_sec, 'version': '1.0.0'}),
    ('B. 不含 appSecret，time=秒',
     {'appKey': APP_KEY, 'time': ts_sec, 'version': '1.0.0'}),
    ('C. 含 appSecret，time=毫秒',
     {'appKey': APP_KEY, 'appSecret': APP_SECRET,
      'time': str(int(time.time() * 1000)), 'version': '1.0.0'}),
]

results = {}
for label, params in variants:
    r = try_token(label, params)
    results[label] = r
    if r and '"token"' in r.lower().replace(' ', ''):
        print('\n>>> ✅ 成功：%s' % label)
        break
    time.sleep(1)

print('\n=== 3. 汇总结论 ===')
for k, v in results.items():
    state = '成功' if (v and '"token"' in v.lower().replace(' ', '')) else '失败'
    print('  %-34s %s' % (k, state))
