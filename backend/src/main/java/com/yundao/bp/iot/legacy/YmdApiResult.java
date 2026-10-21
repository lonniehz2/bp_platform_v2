package com.yundao.bp.iot.legacy;

/**
 * IoT 接口返回（已解密）。
 *
 * @param status   平台状态码，"1" 表示成功
 * @param message  平台消息
 * @param data     解密并反序列化后的业务数据（已由调用方指定类型）
 * @param rawData  原始 data（密文），排障用
 */
public record YmdApiResult<T>(String status, String message, T data, String rawData) {

    public boolean success() {
        return "1".equals(status);
    }
}
