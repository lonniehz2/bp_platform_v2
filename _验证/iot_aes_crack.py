# -*- coding: utf-8 -*-
"""
破解云门道 IoT 的 AES 参数加密方案。

已知（来自接口文档 V2.0.0 §3.3 示例）：
  密钥来源 pwd = token.substring(0, 25) = "5x41nO+EIYENqlj8FmG2XGXMa"   (25 字符)
  明文 userId = "719B29DB1EF45F00D9C5CD320DAE6"                        (29 字符)
  密文（Base64）= "FeBrmAMo+eO63Uuojon/x/1mlWlRhTVL3f+QtwKTEpo="        (32 字节)

29 字节明文 -> 32 字节密文 = PKCS7 填充、块大小 16 => AES。
密钥 25 字节不合法（AES 只接受 16/24/32），故必然存在派生/截断/补位。

本脚本枚举常见实现，用已知明文-密文对判定哪一种正确。
"""
import base64
import hashlib
import itertools

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

PWD = "5x41nO+EIYENqlj8FmG2XGXMa"          # 25 字符
PLAIN = "719B29DB1EF45F00D9C5CD320DAE6"     # 29 字符
EXPECT_B64 = "FeBrmAMo+eO63Uuojon/x/1mlWlRhTVL3f+QtwKTEpo="
EXPECT = base64.b64decode(EXPECT_B64)

print('已知条件：')
print('  pwd      = %r (len=%d)' % (PWD, len(PWD)))
print('  plain    = %r (len=%d)' % (PLAIN, len(PLAIN)))
print('  expect   = %s (len=%d bytes)' % (EXPECT_B64, len(EXPECT)))
print()


# ---------- Java SHA1PRNG（Android/服务端常见）----------
def java_sha1prng_key(seed: bytes, n: int = 16) -> bytes:
    """
    近似 Java SecureRandom("SHA1PRNG") + setSeed(seed) 的输出。
    SHA1PRNG 首次 nextBytes：state = SHA1(seed || counter)，取前 n 字节。
    """
    # 常见实现：digest = SHA1(seed); 若需要更多则继续 SHA1(digest)
    d = hashlib.sha1(seed).digest()
    out = b''
    while len(out) < n:
        out += d
        d = hashlib.sha1(d).digest()
    return out[:n]


# ---------- 候选密钥派生 ----------
candidates = []

# 1) 直接字节（仅当长度合法时才可能）
for n in (16, 24, 32):
    if len(PWD) >= n:
        candidates.append(('截断 %d: pwd[:%d]' % (n, n), PWD[:n].encode()))
    if len(PWD) >= n:
        candidates.append(('截尾 %d: pwd[-%d:]' % (n, n), PWD[-n:].encode()))

# 2) 零填充到 16/24/32
for n in (16, 24, 32):
    if len(PWD) <= n:
        candidates.append(('零填充到 %d' % n, PWD.encode().ljust(n, b'\x00')))

# 3) 哈希派生
candidates.append(('MD5(pwd) 16', hashlib.md5(PWD.encode()).digest()))
candidates.append(('SHA1(pwd)[:16]', hashlib.sha1(PWD.encode()).digest()[:16]))
candidates.append(('SHA256(pwd)[:16]', hashlib.sha256(PWD.encode()).digest()[:16]))
candidates.append(('SHA256(pwd)[:32]', hashlib.sha256(PWD.encode()).digest()))
candidates.append(('MD5(pwd) hex[:16]', hashlib.md5(PWD.encode()).hexdigest()[:16].encode()))
candidates.append(('MD5(pwd) hex[:32]', hashlib.md5(PWD.encode()).hexdigest().encode()))

# 4) Java SHA1PRNG 派生（重点怀疑对象）
candidates.append(('SHA1PRNG(pwd) 16', java_sha1prng_key(PWD.encode(), 16)))
candidates.append(('SHA1PRNG(pwd) 24', java_sha1prng_key(PWD.encode(), 24)))
candidates.append(('SHA1PRNG(pwd) 32', java_sha1prng_key(PWD.encode(), 32)))

# 5) UTF-16LE 字节（Java getBytes("UTF-16LE") 常见坑）
candidates.append(('SHA1PRNG(pwd,UTF16LE) 16',
                   java_sha1prng_key(PWD.encode('utf-16-le'), 16)))
candidates.append(('MD5(pwd,UTF16LE) 16',
                   hashlib.md5(PWD.encode('utf-16-le')).digest()))

# ---------- 候选模式 ----------
MODES = []


def try_modes(key, tag):
    """对给定 key 尝试 ECB / CBC(零IV) / CBC(key前16字节作IV)"""
    pt = PLAIN.encode('utf-8')
    try:
        pad_len = 16 - (len(pt) % 16)
    except Exception:
        return
    padded = pt + bytes([pad_len]) * pad_len

    # ECB
    try:
        c = AES.new(key, AES.MODE_ECB)
        if c.encrypt(padded) == EXPECT:
            MODES.append((tag, 'ECB'))
            return
    except Exception:
        pass

    # CBC + 零 IV
    try:
        c = AES.new(key, AES.MODE_CBC, iv=b'\x00' * 16)
        if c.encrypt(padded) == EXPECT:
            MODES.append((tag, 'CBC/ZeroIV'))
            return
    except Exception:
        pass

    # CBC + key 前 16 字节作 IV
    if len(key) >= 16:
        try:
            c = AES.new(key, AES.MODE_CBC, iv=key[:16])
            if c.encrypt(padded) == EXPECT:
                MODES.append((tag, 'CBC/KeyAsIV'))
                return
        except Exception:
            pass

    # CBC + pwd 前 16 字符作 IV
    try:
        c = AES.new(key, AES.MODE_CBC, iv=PWD[:16].encode().ljust(16, b'\x00'))
        if c.encrypt(padded) == EXPECT:
            MODES.append((tag, 'CBC/PwdAsIV'))
    except Exception:
        pass


print('=== 枚举候选密钥 × 模式 ===')
for tag, key in candidates:
    if len(key) not in (16, 24, 32):
        continue
    try_modes(key, '%s (len=%d)' % (tag, len(key)))
    print('  尝试: %-28s len=%d' % (tag, len(key)))

print()
if MODES:
    print('=' * 72)
    print('✅ 命中！')
    for tag, mode in MODES:
        print('   密钥派生: %s' % tag)
        print('   加密模式: %s' % mode)
    print('=' * 72)
else:
    print('=' * 72)
    print('❌ 未命中。说明派生方式不在枚举范围内。')
    print('   下一步建议：向云门道索取 AES 附件（JAVA 版本）')
    print('=' * 72)
