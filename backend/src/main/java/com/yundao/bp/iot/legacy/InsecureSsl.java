package com.yundao.bp.iot.legacy;

import java.security.SecureRandom;
import java.security.cert.X509Certificate;
import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManager;
import javax.net.ssl.X509TrustManager;

/**
 * 允许自签名证书的 SSLContext。
 *
 * <p>⚠️ <b>仅用于测试/私有化环境</b>。生产环境应把平台证书导入 JVM 信任库
 * 并将 {@code insecure-tls} 置为 false。
 */
final class InsecureSsl {

    private InsecureSsl() {
    }

    static SSLContext context() {
        try {
            TrustManager[] trustAll = new TrustManager[]{
                    new X509TrustManager() {
                        @Override
                        public void checkClientTrusted(X509Certificate[] chain, String authType) {
                        }

                        @Override
                        public void checkServerTrusted(X509Certificate[] chain, String authType) {
                        }

                        @Override
                        public X509Certificate[] getAcceptedIssuers() {
                            return new X509Certificate[0];
                        }
                    }
            };
            SSLContext ctx = SSLContext.getInstance("TLS");
            ctx.init(null, trustAll, new SecureRandom());
            return ctx;
        } catch (Exception e) {
            throw new IllegalStateException("初始化 SSLContext 失败", e);
        }
    }
}
