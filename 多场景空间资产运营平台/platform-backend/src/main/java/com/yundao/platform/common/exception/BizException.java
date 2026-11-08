package com.yundao.platform.common.exception;

public class BizException extends RuntimeException {

    private final String code;
    private final int status;

    public BizException(String code, String message, int status) {
        super(message);
        this.code = code;
        this.status = status;
    }

    public static BizException param(String message) {
        return new BizException("BP40001", message, 400);
    }

    public static BizException notFound(String message) {
        return new BizException("BP40004", message, 404);
    }

    public static BizException conflict(String message) {
        return new BizException("BP40009", message, 409);
    }

    public String getCode() {
        return code;
    }

    public int getStatus() {
        return status;
    }
}
