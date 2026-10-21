# -*- coding: utf-8 -*-
"""计算固定输入的签名，供 Java 侧断言（跨语言契约）"""
import hashlib
import hmac

SECRET = 'unit-test-secret'
METHOD = 'POST'
PATH = '/open/house.list'
TS = '1700000000000'
NONCE = 'abc123'
BODY = '{"pageNum":1}'

payload = '%s\n%s\n%s\n%s\n%s' % (METHOD, PATH, TS, NONCE, BODY)
sig = hmac.new(SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()

print('待签串（转义显示）: %r' % payload)
print('签名              : %s' % sig)
print()
print('把下面常量写进 Java 测试，两边必须一致：')
print('  FIXTURE_SIGN = "%s"' % sig)
