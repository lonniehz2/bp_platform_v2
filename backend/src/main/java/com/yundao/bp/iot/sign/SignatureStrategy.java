package com.yundao.bp.iot.sign;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 签名策略接口（可插拔）—— <b>二期协议框架</b>。
 *
 * <p>设计依据：{@code 02_架构与技术方案.md} §15.3。
 *
 * <p><b>⚠️ 一期使用哪个协议</b>：
 * <ul>
 *   <li><b>一期</b>：现网 AES/MD5 协议 →
 *       {@link com.yundao.bp.iot.legacy.YmdClient}（已实测打通真实平台）</li>
 *   <li><b>二期</b>：本接口 + {@link HmacSha256Strategy} 的 {@code v2-hmac-sha256}，
 *       需 IoT 侧同步改造</li>
 * </ul>
 *
 * <p>决策变更：原 A2 决策为"重新设计协议替换 AES/MD5"；
 * 甲方提供 {@code 算法参考.zip} 后确认现网协议可用，
 * 故一期直用现网协议，本接口作为二期演进预留。
 */
public interface SignatureStrategy {

    /** 协议版本标识，写入 {@code X-Ymd-Proto}。 */
    String protocolVersion();

    /**
     * 生成签名并返回结果（含规范串，便于排障）。
     *
     * <p>实现方负责：补充 timestamp / nonce / keyVersion，计算签名，组装请求头。
     */
    SignResult sign(CanonicalRequest canonical, SignCredentials cred);

    /**
     * 构造请求头（= {@link #sign} 的 headers 部分）。
     *
     * <p>默认实现直接取 {@link SignResult#headers()}；一般无需覆写。
     */
    default Map<String, String> buildHeaders(CanonicalRequest canonical, SignCredentials cred) {
        return sign(canonical, cred).headers();
    }

    /** 单次签名结果（含用于排障的规范串）。 */
    final class SignResult {
        private final Map<String, String> headers;
        private final String canonicalString;
        private final String signature;

        public SignResult(Map<String, String> headers, String canonicalString, String signature) {
            this.headers = headers;
            this.canonicalString = canonicalString;
            this.signature = signature;
        }

        public Map<String, String> headers() {
            return headers;
        }

        public String canonicalString() {
            return canonicalString;
        }

        public String signature() {
            return signature;
        }

        /** 排障用：可打印的规范串。 */
        public String printable() {
            return "===== Canonical Request =====\n"
                    + CanonicalRequest.visualize(canonicalString) + "\n"
                    + "===== Signature =====\n" + signature + "\n";
        }
    }

    /**
     * 校验对端给出的签名（常量时间比较，防时序攻击）。
     */
    boolean verify(String canonicalString, String signature, SignCredentials cred);

    /** 便捷方法：直接把头塞进 Map。 */
    default Map<String, String> headersOf(SignResult r) {
        return new LinkedHashMap<>(r.headers());
    }
}
