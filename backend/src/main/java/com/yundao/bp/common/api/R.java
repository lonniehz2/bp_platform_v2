package com.yundao.bp.common.api;

import java.io.Serializable;
import java.time.Instant;
import java.util.List;

/**
 * 统一响应体。
 *
 * <p>约定（见 {@code 03_API契约.md} §1）：
 * <ul>
 *   <li>成功：{@code code=BP00000}，HTTP 200</li>
 *   <li>失败：HTTP 状态码按 {@link ErrorCode#httpStatus()}，业务码在 {@code code}</li>
 *   <li>{@code messageKey}/{@code args} 供多语言客户端与第三方系统使用；{@code message} 为当前语言文案</li>
 *   <li><b>IoT 回调接口除外</b>：无论成败都必须返回成功（避免重推风暴），见 {@code 02_架构与技术方案.md} §16.3</li>
 * </ul>
 *
 * @param <T> 数据体类型
 */
public record R<T>(String code, String message, String messageKey, List<Object> args,
                   T data, long timestamp) implements Serializable {

    /** 兼容旧的四参数构造（历史调用不关心 messageKey）。 */
    public R(String code, String message, T data, long timestamp) {
        this(code, message, null, List.of(), data, timestamp);
    }

    public static <T> R<T> ok(T data) {
        return new R<>(ErrorCode.SUCCESS.code(), ErrorCode.SUCCESS.message(),
                ErrorCode.SUCCESS.messageKey(), List.of(), data, Instant.now().toEpochMilli());
    }

    public static <T> R<T> ok() {
        return ok(null);
    }

    public static <T> R<T> fail(ErrorCode ec) {
        return new R<>(ec.code(), ec.message(), ec.messageKey(), List.of(), null,
                Instant.now().toEpochMilli());
    }

    public static <T> R<T> fail(ErrorCode ec, String detail) {
        return new R<>(ec.code(), detail == null ? ec.message() : detail,
                ec.messageKey(), List.of(), null, Instant.now().toEpochMilli());
    }

    /** 异常处理器使用：message 为按当前 locale 解析后的文案。 */
    public static <T> R<T> fail(ErrorCode ec, String localizedMessage, String messageKey) {
        return new R<>(ec.code(), localizedMessage, messageKey, List.of(), null,
                Instant.now().toEpochMilli());
    }

    public boolean success() {
        return ErrorCode.SUCCESS.code().equals(code);
    }
}
