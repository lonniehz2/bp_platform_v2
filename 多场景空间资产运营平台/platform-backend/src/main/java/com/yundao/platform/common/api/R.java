package com.yundao.platform.common.api;

public record R<T>(String code, String message, T data, long timestamp) {

    public static <T> R<T> ok(T data) {
        return new R<>("BP00000", "成功", data, System.currentTimeMillis());
    }

    public static <T> R<T> ok() {
        return ok(null);
    }

    public static <T> R<T> error(String code, String message) {
        return new R<>(code, message, null, System.currentTimeMillis());
    }
}
