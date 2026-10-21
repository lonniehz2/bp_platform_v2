package com.yundao.bp.iot.legacy;

/**
 * IoT 接口调用异常。
 */
public class YmdApiException extends RuntimeException {

    /** 平台业务状态码（如 99990002），HTTP/网络异常时为 null */
    private final String status;
    private final int httpStatus;

    public YmdApiException(String message, String status, int httpStatus) {
        super(message);
        this.status = status;
        this.httpStatus = httpStatus;
    }

    public YmdApiException(String message, Throwable cause) {
        super(message, cause);
        this.status = null;
        this.httpStatus = -1;
    }

    public String status() {
        return status;
    }

    public int httpStatus() {
        return httpStatus;
    }
}
