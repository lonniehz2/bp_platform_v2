package com.yundao.bp.common.exception;

import com.yundao.bp.common.api.ErrorCode;

/**
 * 业务异常。由 {@link GlobalExceptionHandler} 统一转换为 {@code R} 响应。
 */
public class BizException extends RuntimeException {

    private final ErrorCode errorCode;

    public BizException(ErrorCode errorCode) {
        super(errorCode.message());
        this.errorCode = errorCode;
    }

    public BizException(ErrorCode errorCode, String detail) {
        super(detail == null ? errorCode.message() : detail);
        this.errorCode = errorCode;
    }

    public BizException(ErrorCode errorCode, String detail, Throwable cause) {
        super(detail == null ? errorCode.message() : detail, cause);
        this.errorCode = errorCode;
    }

    public ErrorCode errorCode() {
        return errorCode;
    }

    // ---------- 常用快捷方法 ----------

    public static BizException of(ErrorCode ec) {
        return new BizException(ec);
    }

    public static BizException of(ErrorCode ec, String detail) {
        return new BizException(ec, detail);
    }

    public static BizException notFound(String what) {
        return new BizException(ErrorCode.NOT_FOUND, what + "不存在");
    }

    public static BizException stateConflict(String detail) {
        return new BizException(ErrorCode.STATE_CONFLICT, detail);
    }

    public static BizException paramInvalid(String detail) {
        return new BizException(ErrorCode.PARAM_INVALID, detail);
    }
}
