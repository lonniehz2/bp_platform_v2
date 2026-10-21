# -*- coding: utf-8 -*-
"""修正：AppSecret 改为可逆加密存储（AES-GCM），供 HMAC 校验时解密"""
import io
import os

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

CIPHER = '''package com.yundao.bp.open.security;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * AppSecret 可逆加密存储。
 *
 * <p><b>为什么不能存哈希</b>：开放平台每次调用都要用 AppSecret 复算 HMAC 签名，
 * 因此密钥必须可还原。存哈希会导致签名永远校验不过。
 *
 * <p><b>为什么不能存明文</b>：数据库被读走等于所有第三方应用被接管。
 *
 * <p>方案：AES-256-GCM（带认证标签，防篡改），密文格式
 * {@code v1:Base64(iv||ciphertext||tag)}。主密钥来自配置项
 * {@code bp.open.secret-key}，<b>私有化部署时必须替换</b>。
 */
@Component
public class SecretCipher {

    private final SecretKeySpec key;
    private static final SecureRandom RANDOM = new SecureRandom();
    private static final int IV_LEN = 12;
    private static final int TAG_BITS = 128;

    public SecretCipher(@Value("${bp.open.secret-key:BP-OPEN-DEFAULT-KEY-PLEASE-CHANGE}")
                        String masterKey) {
        try {
            // 任意长度主密钥 → 32 字节 AES key
            byte[] k = MessageDigest.getInstance("SHA-256")
                    .digest(masterKey.getBytes(StandardCharsets.UTF_8));
            this.key = new SecretKeySpec(k, "AES");
        } catch (Exception e) {
            throw new IllegalStateException("初始化密钥加密器失败", e);
        }
    }

    /** 加密。 */
    public String encrypt(String plain) {
        if (plain == null) {
            return null;
        }
        try {
            byte[] iv = new byte[IV_LEN];
            RANDOM.nextBytes(iv);
            Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.ENCRYPT_MODE, key, new GCMParameterSpec(TAG_BITS, iv));
            byte[] enc = c.doFinal(plain.getBytes(StandardCharsets.UTF_8));
            byte[] all = new byte[iv.length + enc.length];
            System.arraycopy(iv, 0, all, 0, iv.length);
            System.arraycopy(enc, 0, all, iv.length, enc.length);
            return "v1:" + Base64.getEncoder().encodeToString(all);
        } catch (Exception e) {
            throw new IllegalStateException("加密失败", e);
        }
    }

    /** 解密。 */
    public String decrypt(String stored) {
        if (stored == null) {
            return null;
        }
        if (!stored.startsWith("v1:")) {
            // 兼容历史明文（不应出现，但避免直接崩）
            return stored;
        }
        try {
            byte[] all = Base64.getDecoder().decode(stored.substring(3));
            byte[] iv = new byte[IV_LEN];
            System.arraycopy(all, 0, iv, 0, IV_LEN);
            Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(TAG_BITS, iv));
            byte[] dec = c.doFinal(all, IV_LEN, all.length - IV_LEN);
            return new String(dec, StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new IllegalStateException("解密失败（主密钥可能已更换）", e);
        }
    }
}
'''

p = os.path.join(BASE, r'open\security\SecretCipher.java')
os.makedirs(os.path.dirname(p), exist_ok=True)
io.open(p, 'w', encoding='utf-8').write(CIPHER)
print('  + open/security/SecretCipher.java')

# ---- 修正 Impl ----
pi = os.path.join(BASE, r'open\service\impl\OpenPlatformServiceImpl.java')
s = io.open(pi, encoding='utf-8').read()

s = s.replace('import com.yundao.bp.open.security.OpenSigner;',
              'import com.yundao.bp.open.security.OpenSigner;\n'
              'import com.yundao.bp.open.security.SecretCipher;', 1)
s = s.replace('''    private final OpenSigner signer;
    private final SnowflakeIdGenerator idGen;

    public OpenPlatformServiceImpl(OpenAppMapper appMapper, OpenApiMapper apiMapper,
                                   OpenCallLogMapper callLogMapper, OpenSigner signer,
                                   SnowflakeIdGenerator idGen) {
        this.appMapper = appMapper;
        this.apiMapper = apiMapper;
        this.callLogMapper = callLogMapper;
        this.signer = signer;
        this.idGen = idGen;
    }''',
              '''    private final OpenSigner signer;
    private final SecretCipher cipher;
    private final SnowflakeIdGenerator idGen;

    public OpenPlatformServiceImpl(OpenAppMapper appMapper, OpenApiMapper apiMapper,
                                   OpenCallLogMapper callLogMapper, OpenSigner signer,
                                   SecretCipher cipher, SnowflakeIdGenerator idGen) {
        this.appMapper = appMapper;
        this.apiMapper = apiMapper;
        this.callLogMapper = callLogMapper;
        this.signer = signer;
        this.cipher = cipher;
        this.idGen = idGen;
    }''', 1)
# 创建/重置时：加密存储
s = s.replace('''        // 存摘要：即使库被读也拿不到可用密钥（重置才能再获得）
        a.setAppSecret(signer.sign(secret, "bp-open-secret"));''',
              '''        // 加密存储（签名校验需还原明文；不能存哈希）
        a.setAppSecret(cipher.encrypt(secret));''', 1)
s = s.replace('''        String secret = signer.newSecret();
        a.setAppSecret(signer.sign(secret, "bp-open-secret"));''',
              '''        String secret = signer.newSecret();
        a.setAppSecret(cipher.encrypt(secret));''', 1)
# 校验时：解密后复算
s = s.replace('''        String expect = signer.sign(app.getAppSecret(), payload);''',
              '''        String plainSecret = cipher.decrypt(app.getAppSecret());
        String expect = signer.sign(plainSecret, payload);''', 1)
io.open(pi, 'w', encoding='utf-8').write(s)
print('  ✓ OpenPlatformServiceImpl 改用可逆加密（HMAC 可复算）')
