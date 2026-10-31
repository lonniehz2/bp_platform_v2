package com.yundao.bp.common.api;

/**
 * 业务错误码。
 *
 * <p>编码规则：{@code BP} + 5 位数字。前两位表示分类：
 * <ul>
 *   <li>00 成功</li>
 *   <li>10 参数校验</li>
 *   <li>20 认证与权限（含租户越权）</li>
 *   <li>30 资源不存在</li>
 *   <li>40 业务状态冲突</li>
 *   <li>50 协议/签名（IoT）</li>
 *   <li>60 外部依赖</li>
 *   <li>99 系统异常</li>
 * </ul>
 */
public enum ErrorCode {

    SUCCESS("BP00000", "成功", 200),

    PARAM_INVALID("BP10001", "参数校验失败", 400),
    PARAM_MISSING("BP10002", "缺少必要参数", 400),

    UNAUTHORIZED("BP20001", "未登录或登录已过期", 401),
    FORBIDDEN("BP20002", "无权限访问", 403),
    TENANT_MISMATCH("BP20003", "跨租户访问被拒绝", 403),
    /** 租户上下文缺失：绝不允许退化为"查全租户"，必须拒绝。 */
    TENANT_CONTEXT_MISSING("BP20004", "租户上下文缺失", 500),

    NOT_FOUND("BP30001", "资源不存在", 404),
    DUPLICATED("BP30002", "数据已存在", 409),

    STATE_CONFLICT("BP40001", "当前状态不允许该操作", 409),
    OPERATION_NOT_ALLOWED("BP40002", "操作不被允许", 403),

    TIMESTAMP_EXPIRED("BP50001", "请求时间戳超出允许范围", 401),
    REPLAY_DETECTED("BP50002", "疑似重放请求", 401),
    KEY_VERSION_INVALID("BP50003", "密钥版本无效", 401),
    SIGNATURE_INVALID("BP50004", "签名校验失败", 401),
    RESPONSE_SIGNATURE_INVALID("BP50005", "响应签名校验失败", 502),

    IOT_CALL_FAILED("BP60001", "IoT 平台调用失败", 502),
    IOT_RATE_LIMITED("BP60002", "IoT 平台限流", 502),
    IOT_TIMEOUT("BP60003", "IoT 平台超时", 504),

    SYSTEM_ERROR("BP99999", "系统异常", 500);

    private final String code;
    private final String message;
    private final int httpStatus;

    ErrorCode(String code, String message, int httpStatus) {
        this.code = code;
        this.message = message;
        this.httpStatus = httpStatus;
    }

    public String code() {
        return code;
    }

    public String message() {
        return message;
    }

    /** 稳定消息 key；文案由 messages_*.properties 按 locale 解析。 */
    public String messageKey() {
        return "error." + name().toLowerCase(java.util.Locale.ROOT);
    }

    public int httpStatus() {
        return httpStatus;
    }
}
