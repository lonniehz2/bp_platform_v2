package com.yundao.bp.common.api;

import java.io.Serializable;
import java.time.Instant;

/**
 * 统一响应体。
 *
 * <p>约定（见 {@code 03_API契约.md} §1）：
 * <ul>
 *   <li>成功：{@code code=BP00000}，HTTP 200</li>
 *   <li>失败：HTTP 状态码按 {@link ErrorCode#httpStatus()}，业务码在 {@code code}</li>
 *   <li><b>IoT 回调接口除外</b>：无论成败都必须返回成功（避免重推风暴），见 {@code 02_架构与技术方案.md} §16.3</li>
 * </ul>
 *
 * @param <T> 数据体类型
 */
public record R<T>(String code, String message, T data, long timestamp) implements Serializable {

    public static <T> R<T> ok(T data) {
        return new R<>(ErrorCode.SUCCESS.code(), ErrorCode.SUCCESS.message(), data,
                Instant.now().toEpochMilli());
    }

    public static <T> R<T> ok() {
        return ok(null);
    }

    public static <T> R<T> fail(ErrorCode ec) {
        return new R<>(ec.code(), ec.message(), null, Instant.now().toEpochMilli());
    }

    public static <T> R<T> fail(ErrorCode ec, String detail) {
        return new R<>(ec.code(), detail == null ? ec.message() : detail, null,
                Instant.now().toEpochMilli());
    }

    public boolean success() {
        return ErrorCode.SUCCESS.code().equals(code);
    }
}
