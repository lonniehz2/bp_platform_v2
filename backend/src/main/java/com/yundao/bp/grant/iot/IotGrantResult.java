package com.yundao.bp.grant.iot;

import java.util.List;

/**
 * IoT 授权结果。
 *
 * @param iotTaskId 平台异步任务 ID（非空表示需轮询 {@code syncTask/result/list}）
 * @param success   请求是否被接受
 * @param message   平台消息
 * @param devices   逐设备结果（同步返回时可用）
 */
public record IotGrantResult(
        String iotTaskId,
        boolean success,
        String message,
        List<DeviceResult> devices
) {
    public record DeviceResult(String lockId, boolean success, String errorCode,
                               String errorMsg, Integer durationMs) {
    }

    public static IotGrantResult ok(String iotTaskId, String message, List<DeviceResult> devices) {
        return new IotGrantResult(iotTaskId, true, message, devices);
    }

    public static IotGrantResult fail(String message) {
        return new IotGrantResult(null, false, message, List.of());
    }
}
