# -*- coding: utf-8 -*-
"""
云门道 IoT —— 完整客户端（含响应解密）
协议（已全部实测确认）：
  1. token: POST /ymd/auth-service/sys/getAccessToken  (JSON, time=秒, version=1.0.0)
     sign = MD5(sorted k=v&..., appSecret参与, 大写)
  2. 业务接口: 所有业务参数值 AES 加密
     AES: key=PBKDF2WithHmacSHA1(token[:25], salt, 100, 16)
          / AES/CBC/PKCS5Padding / IV="1269571869323221" / Base64
  3. 响应 data 字段亦为 AES 密文，需用同一密钥解密
"""
import base64
import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.request

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

APP_KEY = '4576A20261019122812842505'
APP_SECRET = '1D42A794106300F54B55627F55400A89'
AGENT_CODE = '20261019001'
ORG_ID = '000000003'
BASE = 'https://api.hzbit.cn:4443'

IV = b'1269571869323221'
SALT = b'4BDD60B281D31F1B70EC3AAA81F282BC'
ITER = 100
KEYLEN = 16

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


class YmdClient:
    def __init__(self):
        self.token = None
        self.pwd = None

    # ---------- 密码学 ----------
    @staticmethod
    def _derive(pwd: str) -> bytes:
        return hashlib.pbkdf2_hmac('sha1', pwd.encode('utf-8'), SALT, ITER, KEYLEN)

    def encrypt(self, value: str) -> str:
        c = AES.new(self._derive(self.pwd), AES.MODE_CBC, iv=IV)
        return base64.b64encode(c.encrypt(pad(value.encode('utf-8'), 16))).decode()

    def decrypt(self, b64: str) -> str:
        s = re.sub(r'\s+', '', b64)          # 容忍换行/空格
        c = AES.new(self._derive(self.pwd), AES.MODE_CBC, iv=IV)
        return unpad(c.decrypt(base64.b64decode(s)), 16).decode('utf-8')

    @staticmethod
    def _sign(p: dict) -> str:
        s = '&'.join('%s=%s' % (k, p[k]) for k in sorted(p))
        return hashlib.md5(s.encode('utf-8')).hexdigest().upper()

    @staticmethod
    def _post(path, payload, timeout=30):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(
            BASE + path, data=body, method='POST',
            headers={'Content-Type': 'application/json;charset=UTF-8',
                     'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return r.status, r.read().decode('utf-8', 'replace')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'replace')
        except Exception as e:
            return -1, str(e)

    # ---------- 业务 ----------
    def get_token(self):
        p = {'appKey': APP_KEY, 'appSecret': APP_SECRET,
             'time': str(int(time.time())), 'version': '1.0.0'}
        p['sign'] = self._sign(p)
        _, resp = self._post('/ymd/auth-service/sys/getAccessToken', p)
        j = json.loads(resp)
        if str(j.get('status')) != '1':
            raise RuntimeError('取 token 失败: %s' % resp)
        self.token = j['data']['token']
        self.pwd = self.token[:25]
        return self.token

    def call(self, path, biz_params: dict):
        """所有业务参数值加密；time/token/version 明文"""
        payload = {k: self.encrypt(str(v)) for k, v in biz_params.items()}
        payload['time'] = str(int(time.time()))
        payload['token'] = self.token
        payload['version'] = '1.0.0'
        payload['sign'] = self._sign(payload)
        status, resp = self._post(path, payload)
        j = json.loads(resp)
        data = j.get('data')
        # 响应 data 若为密文则解密
        if isinstance(data, str) and data and str(j.get('status')) == '1':
            try:
                plain = self.decrypt(data)
                try:
                    j['dataDecrypted'] = json.loads(plain)
                except Exception:
                    j['dataDecrypted'] = plain
            except Exception as e:
                j['decryptError'] = str(e)
        return status, j


def main():
    c = YmdClient()

    print('=' * 74)
    print(' 步骤 1 · 获取 Token')
    print('=' * 74)
    t = c.get_token()
    print('  token = %s...' % t[:40])
    print('  pwd   = %r' % c.pwd)
    print('  key   = %s' % c._derive(c.pwd).hex().upper())

    print()
    print('=' * 74)
    print(' 步骤 2 · getPtAgentLocks（agentCode 加密）')
    print('=' * 74)
    print('  agentCode 密文 = %s' % c.encrypt(AGENT_CODE))
    status, j = c.call('/ymd/lockPt-service/pt/getPtAgentLocks',
                       {'agentCode': AGENT_CODE})
    print('  HTTP %d  status=%s  message=%s' % (status, j.get('status'), j.get('message')))

    dec = j.get('dataDecrypted')
    if dec is not None:
        print('\n  ★ 响应已解密：')
        print('  ' + json.dumps(dec, ensure_ascii=False, indent=2)[:2500])
        if isinstance(dec, list):
            print('\n  门锁总数: %d' % len(dec))
            if dec and isinstance(dec[0], dict):
                print('  门锁字段: %s' % sorted(dec[0].keys()))
    elif 'decryptError' in j:
        print('\n  ⚠ 解密失败: %s' % j['decryptError'])
        print('  原始 data 前 200: %s' % str(j.get('data'))[:200])


if __name__ == '__main__':
    main()
